import os
from openai import OpenAI
from src.l3_cognition.model_config import MODEL_ROUTING, get_current_model


class LLMProvider:
    def __init__(self, role="chat"):
        config = MODEL_ROUTING.get(role)

        if not config:
            raise ValueError(f"未在 model_config.py 中找到角色配置: '{role}'")

        self.provider = config.get("provider")
        self.model = config.get("model")
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def _get_active_config(self):
        return get_current_model()

    def get_response(self, messages):
        cfg = self._get_active_config()
        response = self.client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

    def get_response_stream(self, messages):
        cfg = self._get_active_config()
        return self.client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=0.7,
            stream=True
        )
