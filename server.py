import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.config import get_config
from core.provider import LLMProvider
from core.memory_store import MemoryManager
from core.memory import MemorySystem
from core.personality import load_personality
from core.chat_service import ChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

config = get_config()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = LLMProvider()
memory = MemoryManager()
memory_system = MemorySystem(llm, config.db_path, config.memory_dir, config.personality_path)
personality = load_personality(config.personality_path)
chat_service = ChatService(llm, memory, personality, memory_system)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"


class RenameRequest(BaseModel):
    session_id: str
    new_title: str


class SwitchModelRequest(BaseModel):
    model_id: str


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": memory.get_all_sessions()}


@app.post("/api/sessions/rename")
async def rename_session(req: RenameRequest):
    memory.rename_session(req.session_id, req.new_title)
    return {"status": "ok"}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    memory.delete_session(session_id)
    return {"status": "ok"}


@app.get("/api/history")
async def get_history(session_id: str = "default_session"):
    history = memory.get_recent_history(limit=20, session_id=session_id)
    return {"history": history}


@app.get("/api/models")
async def list_models():
    return {
        "models": llm.get_available_models(),
        "current": llm.current_model_id,
    }


@app.post("/api/models/switch")
async def switch_model(req: SwitchModelRequest):
    try:
        llm.switch_model(req.model_id)
        logger.info("模型已切换为: %s", req.model_id)
        return {"status": "ok", "current": llm.current_model_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        reply = chat_service.chat(request.message, request.session_id)
        return {"reply": reply}
    except Exception as e:
        logger.error("聊天请求失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── 记忆系统 API ──

@app.get("/api/memory/profile")
async def get_user_profile():
    return memory_system.user_profile.load()


@app.get("/api/memory/persona")
async def get_persona():
    return memory_system.persona.load()


@app.get("/api/memory/episodic/summaries")
async def get_summaries(limit: int = 10):
    return {"summaries": memory_system.episodic.get_recent_summaries(limit)}


@app.get("/api/memory/episodic/tasks")
async def get_tasks():
    return {"tasks": memory_system.episodic.get_active_tasks()}


@app.get("/api/memory/episodic/events")
async def get_events(event_type: str = None, limit: int = 10):
    return {"events": memory_system.episodic.get_events(event_type, limit)}


@app.get("/api/memory/skills")
async def get_skills():
    return {"skills": memory_system.skills.get_all_skills()}


@app.get("/api/memory/status")
async def get_memory_status():
    return memory_system.get_memory_status()


@app.post("/api/memory/analyze")
async def manual_analyze(session_id: str = "default_session"):
    try:
        messages = memory.get_recent_history(limit=20, session_id=session_id)
        if not messages:
            return {"status": "no_messages"}
        memory_system.process_conversation(session_id, messages)
        return {"status": "ok", "analyzed_messages": len(messages)}
    except Exception as e:
        logger.error("手动分析失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── 前端服务 ──

FRONTEND_DIR = Path(__file__).parent / "frontend"


@app.get("/")
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def check_port(port):
    import subprocess
    import re
    import os

    if os.name != "nt":
        return

    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            check=True,
        )
        pattern = rf":{port}\s+"
        if not re.findall(pattern, result.stdout):
            return

        for line in result.stdout.split("\n"):
            if f":{port}" not in line:
                continue
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                try:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, check=True)
                    logger.info("已终止占用端口 %s 的进程 (PID: %s)", port, pid)
                except subprocess.CalledProcessError:
                    logger.warning("无法终止进程 %s", pid)
    except subprocess.CalledProcessError:
        logger.warning("检查端口占用时出错")


if __name__ == "__main__":
    import uvicorn

    check_port(config.server_port)
    uvicorn.run(app, host=config.server_host, port=config.server_port)
