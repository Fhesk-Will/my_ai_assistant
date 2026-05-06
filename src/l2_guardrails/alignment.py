import logging

from src.common.types import GuardrailResult

logger = logging.getLogger(__name__)


class AlignmentGuardrail:
    """对齐护栏：人格与风格对齐检查（骨架）"""

    def __init__(self, persona_name: str = "灵曦"):
        self.persona_name = persona_name

    def check_alignment(self, response: str) -> GuardrailResult:
        """检查回复是否符合人格设定"""
        # TODO: 实现基于 LLM 的风格一致性检查
        # 当前版本直接通过
        return GuardrailResult(passed=True)
