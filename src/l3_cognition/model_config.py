import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ROUTING = {
    "chat": {
        "provider": "aliyun_bailian",
        "model": "qwen3.6-plus",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    },
}

AVAILABLE_MODELS = [
    {
        "id": "qwen3.6-plus",
        "name": "Qwen3.6 Plus",
        "provider": "阿里云百炼 (DashScope)",
        "model": "qwen-plus",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    },
]

CURRENT_MODEL_ID = "qwen3.6-plus"


def get_model_by_id(model_id: str) -> dict | None:
    for m in AVAILABLE_MODELS:
        if m["id"] == model_id:
            return m
    return None


def get_current_model() -> dict:
    return get_model_by_id(CURRENT_MODEL_ID) or AVAILABLE_MODELS[0]
