from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.l3_cognition.graph import CognitionEngine

router = APIRouter(prefix="/api", tags=["chat"])

_engine: CognitionEngine = None


def init_chat_routes(engine: CognitionEngine):
    global _engine
    _engine = engine


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


class RenameRequest(BaseModel):
    session_id: str
    new_title: str


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        reply = _engine.chat(request.message, request.session_id)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history(session_id: str = "default_session"):
    history = _engine.memory.get_recent_history(limit=20, session_id=session_id)
    return {"history": history}


@router.get("/sessions")
async def list_sessions():
    return {"sessions": _engine.memory.get_all_sessions()}


@router.post("/sessions/rename")
async def rename_session(req: RenameRequest):
    _engine.memory.rename_session(req.session_id, req.new_title)
    return {"status": "ok"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    _engine.memory.delete_session(session_id)
    return {"status": "ok"}
