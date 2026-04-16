import os
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
from core.provider import LLMProvider
from core.memory import MemoryManager

def load_personality():
    """加载性格设定，如果文件不存在则使用默认值"""
    if not os.path.exists("personality.md"):
        return "你是一个高度契合主人的专属AI个人助手，回答简洁、理性且专业。"
    with open("personality.md", "r", encoding="utf-8") as f:
        return f.read()

def main():
    print("正在初始化系统...")
    
    # 1. 实例化大脑与记忆
    llm = LLMProvider(role="chat")  # 默认使用 model_config.py 里的 "chat" 模型
    memory = MemoryManager()
    personality = load_personality()
    
    session_id = "default_session"

    print("✅ AI 助手已启动（输入 'quit' 退出）")
    print("-" * 40)
    
    while True:
        user_input = input("Me: ")
        if user_input.lower() in ['quit', 'exit']:
            print("再见！")
            break
            
        # 2. 将用户的输入存入 SQLite
        memory.add_message(role="user", content=user_input, session_id=session_id)
        
        # 3. 拼装 Prompt 上下文
        messages = [{"role": "system", "content": personality}]
        
        # 提取最近的 10 条对话历史作为短期记忆
        recent_history = memory.get_recent_history(limit=10, session_id=session_id)
        messages.extend(recent_history)
        
        # 4. 调用 API 并处理异常
        try:
            reply = llm.get_response(messages)
            print(f"AI: {reply}")
            
            # 5. 将 AI 的回复也存入 SQLite 形成闭环
            memory.add_message(role="assistant", content=reply, session_id=session_id)
            
        except Exception as e:
            print(f"❌ 调用模型时发生错误: {e}")

if __name__ == "__main__":
    main()