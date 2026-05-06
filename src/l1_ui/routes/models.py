from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/models", tags=["models"])


class SwitchModelRequest(BaseModel):
    model_id: str


@router.get("")
async def list_models():
    # TODO: 接入动态模型管理
    return {"models": [], "current": ""}


@router.post("/switch")
async def switch_model(req: SwitchModelRequest):
    # TODO: 实现模型切换
    return {"status": "ok", "current": req.model_id}
