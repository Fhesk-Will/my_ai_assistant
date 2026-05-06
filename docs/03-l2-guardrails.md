# 03 · L2 护栏层

[← L1 UI 层](02-l1-ui.md) | [← 返回目录](README.md) | [下一页：L3 认知层 →](04-l3-cognition.md)

---

## 概述

L2 护栏层在 LLM 调用的前后各插入一道检查，防止敏感信息进入 LLM 上下文或出现在响应中。架构上是一个可组合的管道，每个检查器独立实现，互不依赖。

---

## 管道结构 `src/l2_guardrails/pipeline.py`

```python
class GuardrailPipeline:
    def __init__(self):
        self.compliance  = ComplianceGuardrail()
        self.factuality  = FactualityGuardrail()
        self.alignment   = AlignmentGuardrail()
        self.self_repair = SelfRepairGuardrail()

    def check_input(self, text: str) -> GuardrailResult:
        # 仅运行合规检查
        return self.compliance.check(text)

    def check_output(self, text: str, query: str = "") -> GuardrailResult:
        # 合规 → 事实性 → 对齐性（串行，任一失败即短路）
        result = self.compliance.check(text)
        if not result.passed:
            return result
        result = self.factuality.check_relevance(query, text)
        if not result.passed:
            return result
        return self.alignment.check_alignment(text)
```

**`GuardrailResult`：**

```python
@dataclass
class GuardrailResult:
    passed: bool
    blocked_reason: str = ""   # 未通过时的原因描述
    sanitized_text: str = ""   # 脱敏后的文本（可选）
```

---

## ComplianceGuardrail `compliance.py`（已完整实现）

### 检测规则

| 类型 | 匹配模式 | 脱敏标签 |
|------|---------|---------|
| API Key | `sk-[A-Za-z0-9]{20,}` / `pk-*` / `api_key-*` | `[API密钥已脱敏]` |
| 身份证号 | `\d{17}[\dX]` | `[身份证号已脱敏]` |
| 手机号 | `1[3-9]\d{9}` | `[手机号已脱敏]` |
| 邮箱 | 标准邮箱正则 | `[邮箱已脱敏]` |
| IP 地址 | `\d{1,3}(\.\d{1,3}){3}` | `[IP地址已脱敏]` |
| 密码字段 | `password=\S+` / `passwd:\S+` 等 | `[密码已脱敏]` |
| 敏感关键词 | 身份证、银行卡号、密码、信用卡、社保号、护照号 | 触发拦截 |

### 两种处理模式

```python
# 模式 1：check() — 检测到敏感信息则拦截，返回 passed=False
result = compliance.check(user_input)
if not result.passed:
    return f"[已拦截] {result.blocked_reason}"

# 模式 2：sanitize_output() — 替换敏感内容后放行（用于输出）
safe_text = compliance.sanitize_output(llm_response)
```

`check_input` 调用 `check()`（拦截），`check_output` 先 `check()` 再 `sanitize_output()`（脱敏放行）。

---

## 骨架检查器（待实现）

### FactualityGuardrail `factuality.py`

```python
def check_relevance(self, query: str, response: str) -> GuardrailResult:
    # TODO: 调用 LLM 判断 response 是否与 query 相关
    return GuardrailResult(passed=True)  # 当前直接放行
```

计划：将 `(query, response)` 发给 LLM，要求返回相关性评分，低于阈值时拦截。

### AlignmentGuardrail `alignment.py`

```python
def check_alignment(self, response: str) -> GuardrailResult:
    # TODO: 检查 response 是否符合人格设定的语气/风格
    return GuardrailResult(passed=True)
```

计划：对比 `PersonaManager` 中的 `tone` 规则，检测风格偏离。

### SelfRepairGuardrail `self_repair.py`

```python
def validate_and_repair(self, response: str, query: str, retry_fn) -> str:
    # TODO: 验证响应质量，不合格时调用 retry_fn 重新生成
    return response
```

计划：定义质量标准（长度、格式、完整性），不达标时最多重试 N 次。

---

## 在 LangGraph 中的调用位置

护栏层不直接被 L1 调用，而是通过 LangGraph 节点触发：

```
guardrail_input 节点  →  pipeline.check_input(user_message)
guardrail_output 节点 →  pipeline.check_output(llm_response, query)
```

详见 [04 · L3 认知层](04-l3-cognition.md) 的图节点说明。

---

[← L1 UI 层](02-l1-ui.md) | [← 返回目录](README.md) | [下一页：L3 认知层 →](04-l3-cognition.md)
