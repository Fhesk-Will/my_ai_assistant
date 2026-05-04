import os

DEFAULT_PERSONALITY = "你是一个高度契合主人的专属AI个人助手，回答简洁、理性且专业。"


def load_personality(path: str = "personality.md") -> str:
    if not os.path.exists(path):
        return DEFAULT_PERSONALITY
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
