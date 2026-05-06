import logging

from src.common.types import GuardrailResult

logger = logging.getLogger(__name__)


class FactualityGuardrail:
    """逻辑与事实护栏：防止答非所问（骨架）"""

    def check_relevance(self, query: str, response: str) -> GuardrailResult:
        """检查回复是否与问题相关"""
        # TODO: 实现基于 LLM 的相关性评估
        # 当前版本直接通过
        return GuardrailResult(passed=True)
