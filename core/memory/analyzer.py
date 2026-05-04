import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """你是一个对话分析专家。请分析以下对话，提取结构化信息。

对话内容：
{conversation}

请严格以 JSON 格式返回分析结果，不要包含任何其他文字。JSON 结构如下：
{{
  "user_facts": {{
    "name": null,
    "occupation": null,
    "location": null,
    "interests": [],
    "technical_skills": [],
    "communication_style": null,
    "other_facts": []
  }},
  "session_summary": "一句话概括本次对话的主要内容",
  "topics": ["话题1", "话题2"],
  "key_events": [
    {{
      "type": "interview|project|learning|personal|work|other",
      "description": "事件描述",
      "date": "YYYY-MM-DD 或 null"
    }}
  ],
  "tasks": [
    {{
      "description": "任务描述",
      "status": "pending|in_progress|completed"
    }}
  ],
  "skills": [
    {{
      "name": "技能名称",
      "description": "技能描述",
      "trigger_patterns": ["触发关键词"],
      "tool_type": "api|script|query"
    }}
  ],
  "persona_adjustments": {{
    "tone": null,
    "rules_to_add": [],
    "rules_to_remove": []
  }}
}}

注意：
- user_facts 中只提取对话中明确提到的事实，不要猜测
- key_events 只记录有明确时间或重要性的事件
- skills 只记录可操作、可复用的技能，普通对话不构成技能
- persona_adjustments 只在发现用户有明确偏好变化时才填写，否则保持 null/空数组
- 如果某个字段没有相关信息，保持默认值（null/空数组）"""


@dataclass
class AnalysisResult:
    user_facts: dict = field(default_factory=dict)
    session_summary: str = ""
    topics: list = field(default_factory=list)
    key_events: list = field(default_factory=list)
    tasks: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    persona_adjustments: dict = field(default_factory=dict)


class MemoryAnalyzer:
    def __init__(self, llm):
        self.llm = llm

    def _format_conversation(self, messages: list[dict]) -> str:
        lines = []
        for msg in messages:
            role = "用户" if msg["role"] == "user" else "助手"
            lines.append(f"[{role}]: {msg['content']}")
        return "\n".join(lines)

    def analyze_conversation(self, messages: list[dict]) -> AnalysisResult:
        if not messages:
            return AnalysisResult()

        conversation = self._format_conversation(messages)
        prompt = ANALYSIS_PROMPT.format(conversation=conversation)

        try:
            llm_messages = [{"role": "user", "content": prompt}]
            response = self.llm.get_response(llm_messages)

            result_dict = self._parse_response(response)
            return AnalysisResult(
                user_facts=result_dict.get("user_facts", {}),
                session_summary=result_dict.get("session_summary", ""),
                topics=result_dict.get("topics", []),
                key_events=result_dict.get("key_events", []),
                tasks=result_dict.get("tasks", []),
                skills=result_dict.get("skills", []),
                persona_adjustments=result_dict.get("persona_adjustments", {}),
            )
        except Exception as e:
            logger.error("对话分析失败: %s", e)
            return AnalysisResult()

    def _parse_response(self, response: str) -> dict:
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning("无法解析 LLM 分析结果: %s", text[:200])
            return {}
