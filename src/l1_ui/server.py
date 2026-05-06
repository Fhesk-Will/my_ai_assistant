import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.l4_data.config import get_config
from src.l3_cognition.provider import LLMProvider
from src.l4_data.memory_store import MemoryManager
from src.l4_data.memory.memory_system import MemorySystem
from src.l2_guardrails import GuardrailPipeline
from src.l3_cognition.graph import CognitionEngine
from src.l1_ui.routes.chat import router as chat_router, init_chat_routes
from src.l1_ui.routes.memory import router as memory_router, init_memory_routes
from src.l1_ui.routes.models import router as models_router
from src.l1_ui.routes.observability import router as observability_router
from src.l1_ui.middleware.metrics import MetricsMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    config = get_config()

    app = FastAPI(title="AI Personal Assistant", version="2.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(MetricsMiddleware)

    # 初始化各层组件
    llm = LLMProvider()
    memory = MemoryManager()
    memory_system = MemorySystem(llm, config.db_path, config.memory_dir, config.personality_path)
    guardrail_pipeline = GuardrailPipeline()

    engine = CognitionEngine(
        llm=llm,
        memory=memory,
        memory_system=memory_system,
        guardrail_pipeline=guardrail_pipeline,
    )

    # 初始化路由依赖
    init_chat_routes(engine)
    init_memory_routes(memory_system, memory)

    # 注册路由
    app.include_router(chat_router)
    app.include_router(memory_router)
    app.include_router(models_router)
    app.include_router(observability_router)

    # 前端静态文件服务
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        @app.get("/")
        async def serve_index():
            index_path = frontend_dir / "dist" / "index.html"
            if not index_path.exists():
                index_path = frontend_dir / "index.html"
            return FileResponse(index_path)

        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            app.mount("/assets", StaticFiles(directory=dist_dir / "assets"), name="assets")
        else:
            app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    return app


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


app = create_app()

if __name__ == "__main__":
    import uvicorn

    config = get_config()
    check_port(config.server_port)
    uvicorn.run(app, host=config.server_host, port=config.server_port)
