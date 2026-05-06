import pytest
from src.l4_data.memory_store import MemoryManager


class TestMemoryManager:
    def test_add_and_retrieve_message(self, memory_manager):
        memory_manager.add_message("user", "你好", session_id="test_session")
        memory_manager.add_message("assistant", "你好！有什么可以帮你的？", session_id="test_session")

        history = memory_manager.get_recent_history(limit=10, session_id="test_session")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_session_management(self, memory_manager):
        memory_manager.update_session_meta("session_1", title="测试会话")
        sessions = memory_manager.get_all_sessions()
        assert len(sessions) == 1
        assert sessions[0]["title"] == "测试会话"

    def test_delete_session(self, memory_manager):
        memory_manager.update_session_meta("session_del", title="待删除")
        memory_manager.add_message("user", "test", session_id="session_del")

        memory_manager.delete_session("session_del")

        sessions = memory_manager.get_all_sessions()
        assert len(sessions) == 0
        history = memory_manager.get_recent_history(session_id="session_del")
        assert len(history) == 0

    def test_rename_session(self, memory_manager):
        memory_manager.update_session_meta("session_rename", title="旧名称")
        memory_manager.rename_session("session_rename", "新名称")

        sessions = memory_manager.get_all_sessions()
        assert sessions[0]["title"] == "新名称"
