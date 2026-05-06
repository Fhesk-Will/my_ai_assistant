import json
import os
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_REGISTRY = {
    "skills": [],
    "version": 1,
}


class SkillRegistryManager:
    def __init__(self, memory_dir: str):
        self.file_path = os.path.join(memory_dir, "skill_registry.json")
        os.makedirs(memory_dir, exist_ok=True)

    def load(self) -> dict:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("加载技能注册表失败: %s", e)
        return DEFAULT_REGISTRY.copy()

    def save(self, registry: dict):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    def register_skill(self, skill_info: dict) -> str:
        registry = self.load()

        for existing in registry["skills"]:
            if existing["name"] == skill_info.get("name"):
                logger.info("技能已存在，跳过注册: %s", skill_info["name"])
                return existing["id"]

        skill_id = f"skill_{uuid.uuid4().hex[:8]}"
        skill = {
            "id": skill_id,
            "name": skill_info.get("name", ""),
            "description": skill_info.get("description", ""),
            "trigger_patterns": skill_info.get("trigger_patterns", []),
            "tool_type": skill_info.get("tool_type", "unknown"),
            "tool_config": skill_info.get("tool_config", {}),
            "proficiency": 0.5,
            "verified": False,
            "usage_count": 0,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
        }

        registry["skills"].append(skill)
        registry["version"] = registry.get("version", 1) + 1
        self.save(registry)
        logger.info("新技能已注册: %s (%s)", skill["name"], skill_id)
        return skill_id

    def update_skill(self, skill_id: str, updates: dict):
        registry = self.load()
        for skill in registry["skills"]:
            if skill["id"] == skill_id:
                skill.update(updates)
                skill["last_used"] = datetime.now().isoformat()
                break
        self.save(registry)

    def verify_skill(self, skill_id: str):
        registry = self.load()
        for skill in registry["skills"]:
            if skill["id"] == skill_id:
                skill["verified"] = True
                skill["proficiency"] = min(1.0, skill["proficiency"] + 0.1)
                break
        self.save(registry)

    def find_skill(self, query: str) -> dict | None:
        registry = self.load()
        query_lower = query.lower()

        best_match = None
        best_score = 0

        for skill in registry["skills"]:
            score = 0
            for pattern in skill.get("trigger_patterns", []):
                if pattern.lower() in query_lower:
                    score += 2

            if skill["name"].lower() in query_lower:
                score += 3

            if score > best_score:
                best_score = score
                best_match = skill

        if best_match and best_score > 0:
            return best_match
        return None

    def get_all_skills(self) -> list:
        registry = self.load()
        return registry.get("skills", [])

    def get_summary(self) -> str:
        skills = self.get_all_skills()
        if not skills:
            return ""

        parts = ["【已掌握的技能】"]
        for s in skills:
            status = "✓" if s.get("verified") else "○"
            parts.append(f"- {status} {s['name']}: {s['description']} (熟练度: {s.get('proficiency', 0):.0%})")

        return "\n".join(parts)
