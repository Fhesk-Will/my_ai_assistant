import os
from openai import OpenAI
from core.model_config import MODEL_ROUTING # 引入新的路由字典

class LLMProvider:
    # 默认调用 "chat" 角色的模型
    def __init__(self, role="chat"): 
        config = MODEL_ROUTING.get(role)
        
        if not config:
            raise ValueError(f"未在 model_config.py 中找到角色配置: '{role}'")
            
        self.provider = config.get("provider")
        self.model = config.get("model")
        api_key = config.get("api_key")
        base_url = config.get("base_url")

        # 初始化兼容 OpenAI 格式的客户端（百炼、小米通用）
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def get_response(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content