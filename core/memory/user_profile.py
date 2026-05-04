import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = {
    "basic": {
        "name": None,
        "occupation": None,
        "location": None,
        "language_preference": "zh",
    },
    "interests": [],
    "technical_skills": [],
    "communication_preferences": {
        "verbosity": "moderate",
        "formality": "casual",
        "emoji_tolerance": "high",
    },
    "interaction_stats": {
        "total_sessions": 0,
        "total_messages": 0,
        "first_interaction": None,
        "last_interaction": None,
    },
    "last_updated": None,
}


class UserProfileManager:
    def __init__(self, memory_dir: str):
        self.file_path = os.path.join(memory_dir, "user_profile.json")
        os.makedirs(memory_dir, exist_ok=True)

    def load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("加载用户画像失败，使用默认值: %s", e)
        return DEFAULT_PROFILE.copy()

    def save(self, profile: dict):
        profile["last_updated"] = datetime.now().isoformat()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def update(self, new_facts: dict):
        profile = self.load()

        if new_facts.get("basic"):
            for key, value in new_facts["basic"].items():
                if value is not None:
                    profile["basic"][key] = value

        for interest in new_facts.get("interests", []):
            if interest not in profile["interests"]:
                profile["interests"].append(interest)

        for skill in new_facts.get("technical_skills", []):
            if skill not in profile["technical_skills"]:
                profile["technical_skills"].append(skill)

        if new_facts.get("communication_style"):
            profile["communication_preferences"]["style"] = new_facts["communication_style"]

        for fact in new_facts.get("other_facts", []):
            key = f"fact_{len([k for k in profile if k.startswith('fact_')])}"
            profile[key] = fact

        self.save(profile)

    def update_stats(self, session_count: int = None, message_count: int = None):
        profile = self.load()
        stats = profile["interaction_stats"]
        now = datetime.now().isoformat()

        if session_count is not None:
            stats["total_sessions"] = session_count
        if message_count is not None:
            stats["total_messages"] = message_count

        if stats["first_interaction"] is None:
            stats["first_interaction"] = now
        stats["last_interaction"] = now

        self.save(profile)

    def get_summary(self) -> str:
        profile = self.load()
        parts = []

        basic = profile.get("basic", {})
        if basic.get("name"):
            parts.append(f"用户名：{basic['name']}")
        if basic.get("occupation"):
            parts.append(f"职业：{basic['occupation']}")
        if basic.get("location"):
            parts.append(f"所在地：{basic['location']}")

        interests = profile.get("interests", [])
        if interests:
            parts.append(f"兴趣爱好：{'、'.join(interests)}")

        skills = profile.get("technical_skills", [])
        if skills:
            parts.append(f"技术栈：{'、'.join(skills)}")

        if not parts:
            return "（暂无用户画像信息）"

        return "【用户画像】\n" + "\n".join(parts)
