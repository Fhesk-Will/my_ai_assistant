# core/model_config.py
import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ROUTING = {
    "chat": {
        "provider": "aliyun_bailian",
        "model": "qwen3.5-35b-a3b",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "base_url": os.getenv("DASHSCOPE_BASE_URL")
    },
    # 以后可以增加
    # "vision": { "provider": "openai", "model": "gpt-4o", ... }
}