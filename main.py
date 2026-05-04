import os
import logging

os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

from core.config import get_config
from core.provider import LLMProvider
from core.memory_store import MemoryManager
from core.memory import MemorySystem
from core.personality import load_personality
from core.chat_service import ChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

config = get_config()

llm = LLMProvider()
memory = MemoryManager()
memory_system = MemorySystem(llm, config.db_path, config.memory_dir, config.personality_path)
personality = load_personality(config.personality_path)
chat_service = ChatService(llm, memory, personality, memory_system)


def main():
    print("正在初始化系统...")
    session_id = "default_session"

    print("AI 助手已启动（输入 'quit' 退出）")
    print("-" * 40)

    while True:
        user_input = input("Me: ")
        if user_input.lower() in ["quit", "exit"]:
            print("再见！")
            break

        try:
            reply = chat_service.chat(user_input, session_id)
            print(f"AI: {reply}")
        except Exception as e:
            print(f"调用模型时发生错误: {e}")


if __name__ == "__main__":
    main()
