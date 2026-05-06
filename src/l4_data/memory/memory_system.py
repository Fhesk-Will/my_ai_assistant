import logging
import threading

from src.l4_data.memory.analyzer import MemoryAnalyzer, AnalysisResult
from src.l4_data.memory.user_profile import UserProfileManager
from src.l4_data.memory.persona import PersonaManager
from src.l4_data.memory.episodic import EpisodicMemoryManager
from src.l4_data.memory.semantic import SemanticMemoryManager
from src.l4_data.memory.skill_registry import SkillRegistryManager

logger = logging.getLogger(__name__)

__all__ = [
    "MemorySystem",
    "MemoryAnalyzer",
    "AnalysisResult",
    "UserProfileManager",
    "PersonaManager",
    "EpisodicMemoryManager",
    "SemanticMemoryManager",
    "SkillRegistryManager",
]


class MemorySystem:
    def __init__(self, llm, db_path: str, memory_dir: str, personality_path: str = "personality.md"):
        self.analyzer = MemoryAnalyzer(llm)
        self.user_profile = UserProfileManager(memory_dir)
        self.persona = PersonaManager(memory_dir, personality_path)
        self.episodic = EpisodicMemoryManager(db_path)
        self.semantic = SemanticMemoryManager(memory_dir + "/chroma")
        self.skills = SkillRegistryManager(memory_dir)

        self.persona.initialize_from_personality_md()
        logger.info("五层记忆系统初始化完成")

    def process_conversation(self, session_id: str, messages: list[dict]):
        try:
            result = self.analyzer.analyze_conversation(messages)

            if result.user_facts:
                self.user_profile.update(result.user_facts)
                logger.info("用户画像已更新")

            if result.session_summary:
                self.episodic.add_summary(
                    session_id=session_id,
                    summary=result.session_summary,
                    topics=result.topics,
                    key_events=[e.get("description", "") for e in result.key_events],
                )

            for event in result.key_events:
                if event.get("description"):
                    self.episodic.add_event(
                        event_type=event.get("type", "other"),
                        description=event["description"],
                        session_id=session_id,
                        event_date=event.get("date"),
                    )

            for task in result.tasks:
                if task.get("description"):
                    self.episodic.add_task(
                        session_id=session_id,
                        description=task["description"],
                        status=task.get("status", "pending"),
                    )

            for skill_info in result.skills:
                if skill_info.get("name"):
                    self.skills.register_skill(skill_info)

            if result.persona_adjustments:
                self.persona.adjust(result.persona_adjustments)

            self.semantic.add_conversation_knowledge(messages)

            logger.info("对话分析完成: summary=%s", result.session_summary[:50] if result.session_summary else "N/A")

        except Exception as e:
            logger.error("对话处理失败: %s", e)

    def process_conversation_async(self, session_id: str, messages: list[dict]):
        thread = threading.Thread(
            target=self.process_conversation,
            args=(session_id, messages),
            daemon=True,
        )
        thread.start()

    def build_system_prompt(self, session_id: str = None, current_query: str = "") -> str:
        parts = []

        user_summary = self.user_profile.get_summary()
        system_prompt = self.persona.get_system_prompt(user_summary)
        parts.append(system_prompt)

        episodic_context = self.episodic.get_context_for_prompt(session_id)
        if episodic_context:
            parts.append(episodic_context)

        if current_query:
            semantic_context = self.semantic.get_context_for_prompt(current_query)
            if semantic_context:
                parts.append(semantic_context)

        skill_summary = self.skills.get_summary()
        if skill_summary:
            parts.append(skill_summary)

        return "\n\n".join(parts)

    def get_memory_status(self) -> dict:
        profile = self.user_profile.load()
        persona = self.persona.load()
        recent_summaries = self.episodic.get_recent_summaries(limit=5)
        active_tasks = self.episodic.get_active_tasks()
        recent_events = self.episodic.get_events(limit=10)
        all_skills = self.skills.get_all_skills()
        semantic_stats = self.semantic.get_stats()

        return {
            "user_profile": {
                "basic": profile.get("basic", {}),
                "interests_count": len(profile.get("interests", [])),
                "skills_count": len(profile.get("technical_skills", [])),
                "interaction_stats": profile.get("interaction_stats", {}),
            },
            "persona": {
                "name": persona.get("name"),
                "version": persona.get("version"),
                "rules_count": len(persona.get("rules", [])),
                "evolution_count": len(persona.get("evolution_log", [])),
            },
            "episodic": {
                "summaries_count": len(recent_summaries),
                "active_tasks_count": len(active_tasks),
                "events_count": len(recent_events),
            },
            "semantic": semantic_stats,
            "skills": {
                "total_count": len(all_skills),
                "verified_count": len([s for s in all_skills if s.get("verified")]),
            },
        }
