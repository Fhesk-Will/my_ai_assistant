import logging

from src.common.types import GuardrailResult
from src.l2_guardrails.compliance import ComplianceGuardrail
from src.l2_guardrails.factuality import FactualityGuardrail
from src.l2_guardrails.alignment import AlignmentGuardrail
from src.l2_guardrails.self_repair import SelfRepairGuardrail

logger = logging.getLogger(__name__)


class GuardrailPipeline:
    """护栏管道：串联所有检查"""

    def __init__(self):
        self.compliance = ComplianceGuardrail()
        self.factuality = FactualityGuardrail()
        self.alignment = AlignmentGuardrail()
        self.self_repair = SelfRepairGuardrail()

    def check_input(self, message: str) -> GuardrailResult:
        """输入护栏：检查用户输入"""
        result = self.compliance.check(message)
        if not result.passed:
            return result

        return GuardrailResult(passed=True)

    def check_output(self, response: str, original_query: str = "") -> GuardrailResult:
        """输出护栏：检查模型回复"""
        # 1. 合规检查（脱敏输出中的敏感信息）
        compliance_result = self.compliance.check(response)
        if not compliance_result.passed:
            sanitized = self.compliance.sanitize_output(response)
            return GuardrailResult(
                passed=True,
                sanitized_content=sanitized,
            )

        # 2. 事实相关性检查
        if original_query:
            fact_result = self.factuality.check_relevance(original_query, response)
            if not fact_result.passed:
                return fact_result

        # 3. 人格对齐检查
        align_result = self.alignment.check_alignment(response)
        if not align_result.passed:
            return align_result

        return GuardrailResult(passed=True)
