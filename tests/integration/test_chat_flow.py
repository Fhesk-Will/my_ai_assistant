import pytest
from unittest.mock import MagicMock, patch

from src.l2_guardrails import GuardrailPipeline
from src.l3_cognition.graph import CognitionEngine
from src.l4_data.memory_store import MemoryManager


class TestChatFlow:
    """集成测试：完整对话流程（使用 mock LLM）"""

    def test_full_chat_flow(self, tmp_path):
        from src.l3_cognition.provider import LLMProvider

        mock_llm = MagicMock(spec=LLMProvider)
        mock_llm.get_response.return_value = "你好！我是灵曦，有什么可以帮你的？"

        db_path = str(tmp_path / "test.db")
        memory = MemoryManager(db_path=db_path)

        guardrail = GuardrailPipeline()

        engine = CognitionEngine(
            llm=mock_llm,
            memory=memory,
            memory_system=None,
            guardrail_pipeline=guardrail,
        )

        reply = engine.chat("你好", session_id="test_session")

        assert reply == "你好！我是灵曦，有什么可以帮你的？"
        mock_llm.get_response.assert_called_once()

        history = memory.get_recent_history(limit=10, session_id="test_session")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_guardrail_blocks_sensitive_input(self, tmp_path):
        from src.l3_cognition.provider import LLMProvider

        mock_llm = MagicMock(spec=LLMProvider)
        db_path = str(tmp_path / "test.db")
        memory = MemoryManager(db_path=db_path)
        guardrail = GuardrailPipeline()

        engine = CognitionEngine(
            llm=mock_llm,
            memory=memory,
            memory_system=None,
            guardrail_pipeline=guardrail,
        )

        reply = engine.chat("我的身份证号是110101199001011234", session_id="test_session")

        assert "拦截" in reply
        mock_llm.get_response.assert_not_called()
