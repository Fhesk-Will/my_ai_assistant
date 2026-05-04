import logging

from core.provider import LLMProvider
from core.memory_store import MemoryManager
from core.memory import MemorySystem

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, llm: LLMProvider, memory: MemoryManager, personality: str,
                 memory_system: MemorySystem = None):
        self.llm = llm
        self.memory = memory
        self.personality = personality
        self.memory_system = memory_system

    def _build_system_prompt(self, session_id: str, current_query: str = "") -> str:
        if self.memory_system:
            return self.memory_system.build_system_prompt(session_id, current_query)
        return self.personality

    def chat(self, message: str, session_id: str = "default_session") -> str:
        history = self.memory.get_recent_history(limit=1, session_id=session_id)
        if not history:
            title = message[:15] + ("..." if len(message) > 15 else "")
            self.memory.update_session_meta(session_id, title=title)
        else:
            self.memory.update_session_meta(session_id)

        self.memory.add_message(role="user", content=message, session_id=session_id)

        system_prompt = self._build_system_prompt(session_id, message)
        messages = [{"role": "system", "content": system_prompt}]
        history = self.memory.get_recent_history(limit=10, session_id=session_id)
        messages.extend(history)

        reply = self.llm.get_response(messages)
        logger.info("模型回复成功: %s", reply[:80])

        self.memory.add_message(role="assistant", content=reply, session_id=session_id)

        if self.memory_system:
            recent = self.memory.get_recent_history(limit=20, session_id=session_id)
            self.memory_system.process_conversation_async(session_id, recent)

        return reply
