import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

_metrics_store: list[dict] = []
MAX_METRICS = 1000


class MetricsMiddleware(BaseHTTPMiddleware):
    """Token/状态/链路追踪中间件（骨架）"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time
        metric = {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": time.time(),
        }

        _metrics_store.append(metric)
        if len(_metrics_store) > MAX_METRICS:
            _metrics_store.pop(0)

        return response


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
