import logging

from src.l4_data.memory.memory_system import MemorySystem

logger = logging.getLogger(__name__)


class ContextManager:
    """动态上下文管理：从记忆系统提取相关上下文"""

    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system

    def build_context(self, session_id: str, query: str) -> str:
        return self.memory_system.build_system_prompt(session_id, query)

    def process_after_response(self, session_id: str, messages: list[dict]):
        self.memory_system.process_conversation_async(session_id, messages)
