import logging

from src.l3_cognition.provider import LLMProvider
from src.l4_data.memory_store import MemoryManager
from src.l4_data.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)


def chat_node(state: dict) -> dict:
    """对话节点：构建 prompt、调用 LLM、返回回复"""
    llm: LLMProvider = state["_llm"]
    memory: MemoryManager = state["_memory"]
    memory_system: MemorySystem = state.get("_memory_system")

    message = state["message"]
    session_id = state["session_id"]

    history = memory.get_recent_history(limit=1, session_id=session_id)
    if not history:
        title = message[:15] + ("..." if len(message) > 15 else "")
        memory.update_session_meta(session_id, title=title)
    else:
        memory.update_session_meta(session_id)

    memory.add_message(role="user", content=message, session_id=session_id)

    system_prompt = state.get("context", "")
    if not system_prompt and memory_system:
        system_prompt = memory_system.build_system_prompt(session_id, message)

    messages = [{"role": "system", "content": system_prompt}]
    history = memory.get_recent_history(limit=10, session_id=session_id)
    messages.extend(history)

    reply = llm.get_response(messages)
    logger.info("模型回复成功: %s", reply[:80])

    memory.add_message(role="assistant", content=reply, session_id=session_id)

    if memory_system:
        recent = memory.get_recent_history(limit=20, session_id=session_id)
        memory_system.process_conversation_async(session_id, recent)

    state["response"] = reply
    return state
