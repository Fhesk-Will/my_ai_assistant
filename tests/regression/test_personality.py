import pytest
from unittest.mock import MagicMock

from src.l2_guardrails.alignment import AlignmentGuardrail


class TestPersonalityRegression:
    """人格一致性回归测试"""

    def test_alignment_guardrail_passes_normal(self):
        guardrail = AlignmentGuardrail(persona_name="灵曦")
        result = guardrail.check_alignment("你好！我是灵曦，很高兴认识你。")
        assert result.passed is True

    def test_persona_system_prompt_contains_name(self):
        from src.l4_data.memory.persona import PersonaManager
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PersonaManager(tmpdir, personality_path="nonexistent.md")
            manager.initialize_from_personality_md()

            prompt = manager.get_system_prompt()
            assert "灵曦" in prompt

    def test_persona_rules_in_prompt(self):
        from src.l4_data.memory.persona import PersonaManager
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PersonaManager(tmpdir, personality_path="nonexistent.md")
            manager.initialize_from_personality_md()

            prompt = manager.get_system_prompt()
            assert "对话原则" in prompt
            assert "结构清晰" in prompt
