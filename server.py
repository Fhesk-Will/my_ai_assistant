# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.provider import LLMProvider
from core.memory import MemoryManager
import os
import uuid

app = FastAPI()

# 解决跨域问题（前端访问后端必备）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议指定具体域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化业务模块
llm = LLMProvider(role="chat")
memory = MemoryManager()

# 定义请求数据模型
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

class RenameRequest(BaseModel):
    session_id: str
    new_title: str

@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": memory.get_all_sessions()}

@app.post("/api/sessions/rename")
async def rename_session(req: RenameRequest):
    memory.rename_session(req.session_id, req.new_title)
    return {"status": "ok"}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    memory.delete_session(session_id)
    return {"status": "ok"}

@app.get("/api/history")
async def get_history(session_id: str = "default_session"):
    """获取历史记录用于前端初始化渲染"""
    history = memory.get_recent_history(limit=20, session_id=session_id)
    return {"history": history}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 如果是该会话的第一条消息，将消息前10个字存为标题
        history = memory.get_recent_history(limit=1, session_id=request.session_id)
        if not history:
            title = request.message[:15] + ("..." if len(request.message) > 15 else "")
            memory.update_session_meta(request.session_id, title=title)
        else:
            memory.update_session_meta(request.session_id) # 仅更新活跃时间
        
        # 1. 存入用户消息
        memory.add_message(role="user", content=request.message, session_id=request.session_id)
        
        # 2. 构造上下文
        personality = "你是一个高度契合主人的专属AI个人助手。" # 建议从 personality.md 读取
        messages = [{"role": "system", "content": personality}]
        history = memory.get_recent_history(limit=10, session_id=request.session_id)
        messages.extend(history)
        
        # 3. 调用 AI 大模型
        reply = llm.get_response(messages)

        print(f"[模型回复成功]: {reply}\n")
        
        # 4. 存入 AI 回复
        memory.add_message(role="assistant", content=reply, session_id=request.session_id)
        
        return {"reply": reply}
    except Exception as e:
        print(f"[报错]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def check_port(port):
    """检查端口是否被占用，如果被占用则终止占用该端口的进程"""
    import os
    import subprocess
    import re
    
    # 在 Windows 上使用 netstat 命令检查端口占用
    if os.name == 'nt':
        try:
            # 执行 netstat 命令获取端口占用情况
            result = subprocess.run(
                ['netstat', '-ano'], 
                capture_output=True, 
                text=True,
                check=True
            )
            
            # 搜索占用指定端口的进程
            pattern = rf':{port}\s+'
            matches = re.findall(pattern, result.stdout)
            
            if matches:
                # 提取进程 ID
                process_lines = [line for line in result.stdout.split('\n') if f':{port}' in line]
                for line in process_lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            # 终止占用端口的进程
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                check=True
                            )
                            print(f"已终止占用端口 {port} 的进程 (PID: {pid})")
                        except subprocess.CalledProcessError:
                            print(f"无法终止进程 {pid}")
        except subprocess.CalledProcessError:
            print("检查端口占用时出错")

if __name__ == "__main__":
    import uvicorn
    port = 8000
    
    # 检查并清理端口
    check_port(port)
    
    # 启动服务器
    uvicorn.run(app, host="0.0.0.0", port=port)