import os
import re
from dataclasses import dataclass, field
from dotenv import load_dotenv

import yaml

load_dotenv()


@dataclass
class ModelConfig:
    id: str
    label: str
    provider_id: str
    provider_label: str
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.7


@dataclass
class AppConfig:
    db_path: str = "data/db/assistant_memory.db"
    personality_path: str = "personality.md"
    memory_dir: str = "data/memory"
    chroma_path: str = "data/memory/chroma"
    analysis_batch_size: int = 5
    memory_retrieval_limit: int = 5
    server_host: str = "127.0.0.1"
    server_port: int = 8888
    cors_origins: list = field(default_factory=lambda: ["*"])
    models: dict = field(default_factory=dict)
    default_model_id: str = ""


def _resolve_env_vars(value: str) -> str:
    return re.sub(r"\$\{(\w+)}", lambda m: os.getenv(m.group(1), ""), value)


def _load_models(path: str = "models.yaml") -> tuple[dict, str]:
    if not os.path.exists(path):
        return {}, ""

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    models = {}
    providers = data.get("providers", {})
    for provider_id, provider in providers.items():
        api_key = _resolve_env_vars(provider.get("api_key", ""))
        base_url = _resolve_env_vars(provider.get("base_url", ""))
        provider_label = provider.get("label", provider_id)

        for m in provider.get("models", []):
            global_id = f"{provider_id}/{m['id']}"
            models[global_id] = ModelConfig(
                id=global_id,
                label=m.get("label", m["id"]),
                provider_id=provider_id,
                provider_label=provider_label,
                model=m["id"],
                api_key=api_key,
                base_url=base_url,
                temperature=float(m.get("temperature", 0.7)),
            )

    default = data.get("default", "")
    if default and default not in models:
        default = next(iter(models), "")

    return models, default


def get_config() -> AppConfig:
    models, default_id = _load_models()
    return AppConfig(
        db_path=os.getenv("DB_PATH", "data/db/assistant_memory.db"),
        personality_path=os.getenv("PERSONALITY_PATH", "personality.md"),
        memory_dir=os.getenv("MEMORY_DIR", "data/memory"),
        chroma_path=os.getenv("CHROMA_PATH", "data/memory/chroma"),
        analysis_batch_size=int(os.getenv("ANALYSIS_BATCH_SIZE", "5")),
        memory_retrieval_limit=int(os.getenv("MEMORY_RETRIEVAL_LIMIT", "5")),
        server_host=os.getenv("SERVER_HOST", "127.0.0.1"),
        server_port=int(os.getenv("SERVER_PORT", "8888")),
        cors_origins=os.getenv("CORS_ORIGINS", "*").split(","),
        models=models,
        default_model_id=default_id,
    )
