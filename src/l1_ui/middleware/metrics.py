import logging
import time
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

_metrics_store: list[dict] = []
MAX_METRICS = 1000

STREAM_PATHS = {"/api/chat/stream"}


class MetricsMiddleware:
    """Token/状态/链路追踪中间件 - 使用原生 ASGI 避免缓冲流式响应"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "")
        start_time = time.time()
        status_code = 0

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration = time.time() - start_time
        metric = {
            "path": path,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": time.time(),
        }

        _metrics_store.append(metric)
        if len(_metrics_store) > MAX_METRICS:
            _metrics_store.pop(0)


def get_recent_metrics(limit: int = 50) -> list[dict]:
    return _metrics_store[-limit:]


def get_metrics_summary() -> dict:
    if not _metrics_store:
        return {"total_requests": 0, "avg_duration_ms": 0}

    total = len(_metrics_store)
    avg_duration = sum(m["duration_ms"] for m in _metrics_store) / total

    return {
        "total_requests": total,
        "avg_duration_ms": round(avg_duration, 2),
        "recent_errors": len([m for m in _metrics_store[-100:] if m["status_code"] >= 400]),
    }
