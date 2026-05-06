from fastapi import APIRouter
from pydantic import BaseModel

from src.l1_ui.middleware.metrics import get_recent_metrics, get_metrics_summary

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/metrics")
async def get_metrics(limit: int = 50):
    return {"metrics": get_recent_metrics(limit)}


@router.get("/summary")
async def get_summary():
    return get_metrics_summary()
