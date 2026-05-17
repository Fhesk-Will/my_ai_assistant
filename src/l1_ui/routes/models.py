from fastapi import APIRouter
from pydantic import BaseModel

from src.l3_cognition.model_config import (
    AVAILABLE_MODELS,
    CURRENT_MODEL_ID,
    get_model_by_id,
)
from src.l3_cognition.provider import LLMProvider

router = APIRouter(prefix="/api/models", tags=["models"])

_llm: LLMProvider = None


def init_models_routes(llm: LLMProvider):
    global _llm
    _llm = llm


class SwitchModelRequest(BaseModel):
    model_id: str


@router.get("")
async def list_models():
    models = [
        {
            "id": m["id"],
            "name": m["name"],
            "provider": m["provider"],
        }
        for m in AVAILABLE_MODELS
    ]
    return {"models": models, "current": CURRENT_MODEL_ID}


@router.post("/switch")
async def switch_model(req: SwitchModelRequest):
    import src.l3_cognition.model_config as cfg

    new_model = get_model_by_id(req.model_id)
    if not new_model:
        return {"status": "error", "message": f"未找到模型: {req.model_id}"}

    cfg.CURRENT_MODEL_ID = req.model_id

    if _llm and (
        new_model["api_key"] != _llm.client.api_key
        or new_model["base_url"] != str(_llm.client.base_url)
    ):
        from openai import OpenAI
        _llm.client = OpenAI(
            api_key=new_model["api_key"],
            base_url=new_model["base_url"],
        )

    return {"status": "ok", "current": req.model_id}
