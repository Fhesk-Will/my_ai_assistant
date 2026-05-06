import re
import logging

from src.common.types import GuardrailResult

logger = logging.getLogger(__name__)

SENSITIVE_PATTERNS = [
    (r"\b[A-Za-z]{2,5}-[A-Za-z0-9]{20,}\b", "API Key"),
    (r"\b\d{17}[\dXx]\b", "身份证号"),
    (r"\b\d{11}\b", "手机号"),
    (r"[\w.-]+@[\w.-]+\.\w+", "邮箱地址"),
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "IP地址"),
    (r"(?:sk|pk|api[_-]?key)[_-]?[a-zA-Z0-9]{16,}", "API密钥"),
    (r"(?:password|passwd|pwd)\s*[:=]\s*\S+", "密码"),
]

SENSITIVE_KEYWORDS = [
    "身份证", "银行卡号", "密码", "信用卡",
    "社保号", "护照号",
]


class ComplianceGuardrail:
    """合规与安全护栏：拦截敏感词、Key、私密信息"""

    def __init__(self):
        self._patterns = [(re.compile(p, re.IGNORECASE), label) for p, label in SENSITIVE_PATTERNS]

    def check(self, text: str) -> GuardrailResult:
        for pattern, label in self._patterns:
            match = pattern.search(text)
            if match:
                logger.warning("合规拦截: 检测到 %s", label)
                return GuardrailResult(
                    passed=False,
                    blocked_reason=f"检测到敏感信息（{label}），已拦截",
                )

        text_lower = text.lower()
        for keyword in SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                logger.warning("合规拦截: 检测到敏感关键词 '%s'", keyword)
                return GuardrailResult(
                    passed=False,
                    blocked_reason=f"包含敏感关键词（{keyword}），请注意信息安全",
                )

        return GuardrailResult(passed=True)

    def sanitize_output(self, text: str) -> str:
        """对输出中的敏感信息进行脱敏"""
        sanitized = text
        for pattern, label in self._patterns:
            sanitized = pattern.sub(f"[{label}已脱敏]", sanitized)
        return sanitized
