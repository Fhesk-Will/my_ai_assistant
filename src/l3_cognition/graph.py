import logging
from typing import Any

from langgraph.graph import StateGraph, END

from src.l2_guardrails import GuardrailPipeline
from src.l3_cognition.nodes.memory_node import memory_node
from src.l3_cognition.nodes.chat_node import chat_node
from src.l3_cognition.provider import LLMProvider
from src.l4_data.memory_store import MemoryManager
from src.l4_data.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)


def _guardrail_input_node(state: dict) -> dict:
    """输入护栏节点"""
    pipeline: GuardrailPipeline = state.get("_guardrail_pipeline")
    if not pipeline:
        return state

    result = pipeline.check_input(state["message"])
    state["guardrail_input"] = result.model_dump()

    if not result.passed:
        state["response"] = f"[已拦截] {result.blocked_reason}"
    return state


def _guardrail_output_node(state: dict) -> dict:
    """输出护栏节点"""
    pipeline: GuardrailPipeline = state.get("_guardrail_pipeline")
    if not pipeline or not state.get("response"):
        return state

    result = pipeline.check_output(state["response"], state["message"])
    state["guardrail_output"] = result.model_dump()

    if not result.passed and result.sanitized_content:
        state["response"] = result.sanitized_content
    return state


def _should_continue_after_input_guard(state: dict) -> str:
    """输入护栏后的路由：被拦截则直接结束，否则继续"""
    guard_result = state.get("guardrail_input", {})
    if guard_result and not guard_result.get("passed", True):
        return "blocked"
    return "continue"


def build_graph(
    llm: LLMProvider,
    memory: MemoryManager,
    memory_system: MemorySystem = None,
    guardrail_pipeline: "GuardrailPipeline" = None,
) -> Any:
    """构建 LangGraph 对话流程图"""

    def inject_deps(state: dict) -> dict:
        state["_llm"] = llm
        state["_memory"] = memory
        state["_memory_system"] = memory_system
        state["_guardrail_pipeline"] = guardrail_pipeline
        return state

    graph = StateGraph(dict)

    graph.add_node("inject_deps", inject_deps)
    graph.add_node("guardrail_input", _guardrail_input_node)
    graph.add_node("memory_retrieve", memory_node)
    graph.add_node("chat", chat_node)
    graph.add_node("guardrail_output", _guardrail_output_node)

    graph.set_entry_point("inject_deps")
    graph.add_edge("inject_deps", "guardrail_input")

    graph.add_conditional_edges(
        "guardrail_input",
        _should_continue_after_input_guard,
        {
            "blocked": END,
            "continue": "memory_retrieve",
        },
    )

    graph.add_edge("memory_retrieve", "chat")
    graph.add_edge("chat", "guardrail_output")
    graph.add_edge("guardrail_output", END)

    return graph.compile()


class CognitionEngine:
    """L3 认知引擎：封装 LangGraph 流程"""

    def __init__(
        self,
        llm: LLMProvider,
        memory: MemoryManager,
        memory_system: MemorySystem = None,
        guardrail_pipeline: "GuardrailPipeline" = None,
    ):
        self.llm = llm
        self.memory = memory
        self.memory_system = memory_system
        self.guardrail_pipeline = guardrail_pipeline
        self._graph = build_graph(llm, memory, memory_system, guardrail_pipeline)

    def chat(self, message: str, session_id: str = "default_session") -> str:
        initial_state = {
            "message": message,
            "session_id": session_id,
            "history": [],
            "context": "",
            "response": "",
            "metrics": {},
            "guardrail_input": {},
            "guardrail_output": {},
        }

        result = self._graph.invoke(initial_state)
        return result.get("response", "")
