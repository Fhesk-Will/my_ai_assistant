import pytest
from src.l2_guardrails import GuardrailPipeline
from src.l2_guardrails.compliance import ComplianceGuardrail


class TestComplianceGuardrail:
    def setup_method(self):
        self.guardrail = ComplianceGuardrail()

    def test_pass_normal_text(self):
        result = self.guardrail.check("你好，今天天气怎么样？")
        assert result.passed is True

    def test_block_id_number(self):
        result = self.guardrail.check("我的身份证号是110101199001011234")
        assert result.passed is False
        assert "身份证" in result.blocked_reason

    def test_block_api_key_pattern(self):
        result = self.guardrail.check("我的密钥是 sk-abc123def456ghi789jkl012mno345")
        assert result.passed is False

    def test_block_sensitive_keyword(self):
        result = self.guardrail.check("帮我查一下银行卡号对应的信息")
        assert result.passed is False
        assert "银行卡号" in result.blocked_reason

    def test_sanitize_output(self):
        text = "你的API密钥是 sk-abc123def456ghi789jkl012"
        sanitized = self.guardrail.sanitize_output(text)
        assert "sk-abc123" not in sanitized
        assert "已脱敏" in sanitized


class TestGuardrailPipeline:
    def setup_method(self):
        self.pipeline = GuardrailPipeline()

    def test_input_pass(self):
        result = self.pipeline.check_input("帮我写一段Python代码")
        assert result.passed is True

    def test_input_block(self):
        result = self.pipeline.check_input("我的身份证号是110101199001011234")
        assert result.passed is False

    def test_output_pass(self):
        result = self.pipeline.check_output("这是一段正常的回复内容。", "你好")
        assert result.passed is True
