import os
import logging
from datetime import datetime

import yaml

logger = logging.getLogger(__name__)

DEFAULT_PERSONA = {
    "version": 1,
    "name": "灵曦",
    "base_personality": "温暖、耐心、富有好奇心",
    "tone": {
        "default": "温柔专业",
        "technical": "准确严谨",
        "casual": "轻松幽默",
    },
    "rules": [
        "回答结构清晰，重要观点分点说明",
        "技术解释准确但易懂",
        "保持专业的同时展现个性",
    ],
    "evolution_log": [],
}


class PersonaManager:
    def __init__(self, memory_dir: str, personality_path: str = "personality.md"):
        self.file_path = os.path.join(memory_dir, "persona_manifest.yaml")
        self.personality_path = personality_path
        os.makedirs(memory_dir, exist_ok=True)

    def load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or DEFAULT_PERSONA.copy()
            except (yaml.YAMLError, IOError) as e:
                logger.warning("加载人格配置失败，使用默认值: %s", e)
        return DEFAULT_PERSONA.copy()

    def save(self, persona: dict):
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml.dump(persona, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    def initialize_from_personality_md(self):
        if os.path.exists(self.file_path):
            return

        persona = DEFAULT_PERSONA.copy()
        if os.path.exists(self.personality_path):
            try:
                with open(self.personality_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                persona["base_from_md"] = md_content
            except IOError:
                pass

        self.save(persona)
        logger.info("从 personality.md 初始化人格配置完成")

    def adjust(self, adjustments: dict):
        if not adjustments:
            return

        persona = self.load()
        changed = False

        if adjustments.get("tone") and adjustments["tone"] is not None:
            persona["tone"]["adjusted"] = adjustments["tone"]
            changed = True

        for rule in adjustments.get("rules_to_add", []):
            if rule and rule not in persona["rules"]:
                persona["rules"].append(rule)
                changed = True

        for rule in adjustments.get("rules_to_remove", []):
            if rule in persona["rules"]:
                persona["rules"].remove(rule)
                changed = True

        if changed:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "adjustments": adjustments,
            }
            persona["evolution_log"].append(entry)
            persona["version"] = persona.get("version", 1) + 1
            self.save(persona)
            logger.info("人格配置已更新: %s", adjustments)

    def get_system_prompt(self, user_profile_summary: str = "") -> str:
        persona = self.load()

        parts = []

        if os.path.exists(self.personality_path):
            try:
                with open(self.personality_path, "r", encoding="utf-8") as f:
                    parts.append(f.read())
            except IOError:
                parts.append(f"你是{persona['name']}，{persona['base_personality']}。")
        else:
            parts.append(f"你是{persona['name']}，{persona['base_personality']}。")

        tone = persona.get("tone", {})
        if tone:
            tone_desc = "、".join(f"{k}风格：{v}" for k, v in tone.items() if v)
            parts.append(f"说话风格：{tone_desc}。")

        rules = persona.get("rules", [])
        if rules:
            parts.append("对话原则：" + "；".join(rules) + "。")

        if user_profile_summary and user_profile_summary != "（暂无用户画像信息）":
            parts.append(user_profile_summary)

        return "\n\n".join(parts)
