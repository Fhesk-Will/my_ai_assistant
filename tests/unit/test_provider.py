import pytest
from unittest.mock import MagicMock


class TestLLMProvider:
    def test_provider_init_invalid_role(self):
        from src.l3_cognition.provider import LLMProvider
        with pytest.raises(ValueError, match="未在 model_config.py 中找到角色配置"):
            LLMProvider(role="nonexistent_role")

    def test_provider_get_response_mock(self):
        from src.l3_cognition.provider import LLMProvider

        provider = LLMProvider.__new__(LLMProvider)
        provider.client = MagicMock()
        provider.model = "test-model"

        mock_choice = MagicMock()
        mock_choice.message.content = "测试回复"
        provider.client.chat.completions.create.return_value = MagicMock(
            choices=[mock_choice]
        )

        result = provider.get_response([{"role": "user", "content": "你好"}])
        assert result == "测试回复"
        provider.client.chat.completions.create.assert_called_once()
