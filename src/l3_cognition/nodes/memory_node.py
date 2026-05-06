import logging

from src.l4_data.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)


def memory_node(state: dict) -> dict:
    """记忆提取节点：从记忆系统获取相关上下文"""
    memory_system: MemorySystem = state.get("_memory_system")
    if not memory_system:
        return state

    session_id = state["session_id"]
    message = state["message"]

    context = memory_system.build_system_prompt(session_id, message)
    state["context"] = context
    return state
