from fastapi import APIRouter, HTTPException

from src.l4_data.memory.memory_system import MemorySystem
from src.l4_data.memory_store import MemoryManager

router = APIRouter(prefix="/api/memory", tags=["memory"])

_memory_system: MemorySystem = None
_memory_store: MemoryManager = None


def init_memory_routes(memory_system: MemorySystem, memory_store: MemoryManager):
    global _memory_system, _memory_store
    _memory_system = memory_system
    _memory_store = memory_store


@router.get("/profile")
async def get_user_profile():
    return _memory_system.user_profile.load()


@router.get("/persona")
async def get_persona():
    return _memory_system.persona.load()


@router.get("/episodic/summaries")
async def get_summaries(limit: int = 10):
    return {"summaries": _memory_system.episodic.get_recent_summaries(limit)}


@router.get("/episodic/tasks")
async def get_tasks():
    return {"tasks": _memory_system.episodic.get_active_tasks()}


@router.get("/episodic/events")
async def get_events(event_type: str = None, limit: int = 10):
    return {"events": _memory_system.episodic.get_events(event_type, limit)}


@router.get("/skills")
async def get_skills():
    return {"skills": _memory_system.skills.get_all_skills()}


@router.get("/status")
async def get_memory_status():
    return _memory_system.get_memory_status()


@router.post("/analyze")
async def manual_analyze(session_id: str = "default_session"):
    try:
        messages = _memory_store.get_recent_history(limit=20, session_id=session_id)
        if not messages:
            return {"status": "no_messages"}
        _memory_system.process_conversation(session_id, messages)
        return {"status": "ok", "analyzed_messages": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
