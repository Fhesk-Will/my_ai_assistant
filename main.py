import os
import sys
import logging

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.l4_data.config import get_config
from src.l3_cognition.provider import LLMProvider
from src.l4_data.memory_store import MemoryManager
from src.l4_data.memory.memory_system import MemorySystem
from src.l2_guardrails import GuardrailPipeline
from src.l3_cognition.graph import CognitionEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    config = get_config()

    llm = LLMProvider()
    memory = MemoryManager()
    memory_system = MemorySystem(llm, config.db_path, config.memory_dir, config.personality_path)
    guardrail_pipeline = GuardrailPipeline()

    engine = CognitionEngine(
        llm=llm,
        memory=memory,
        memory_system=memory_system,
        guardrail_pipeline=guardrail_pipeline,
    )

    print("AI 助手已启动（输入 'quit' 退出）")
    print("-" * 40)

    session_id = "default_session"

    while True:
        user_input = input("Me: ")
        if user_input.lower() in ["quit", "exit"]:
            print("再见！")
            break

        try:
            reply = engine.chat(user_input, session_id)
            print(f"AI: {reply}")
        except Exception as e:
            print(f"调用模型时发生错误: {e}")


if __name__ == "__main__":
    main()
