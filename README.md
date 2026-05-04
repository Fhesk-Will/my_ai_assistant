# My AI Assistant

基于 Python + FastAPI 的 AI 聊天助手，前端使用 Vue 3 单文件 SPA，后端调用阿里云百炼平台的通义千问大模型。

## 架构

```
前端 (Vue 3 + Tailwind CSS) ──HTTP──> 后端 (FastAPI) ──OpenAI 兼容协议──> 阿里云百炼 (通义千问)
                                            │
                                        SQLite 持久化
```

## 项目结构

```
├── server.py                # Web 入口 — 只含 FastAPI 路由，调用 service 层
├── main.py                  # CLI 入口 — 终端 REPL，调用 service 层
├── core/
│   ├── config.py            # 集中配置（从 .env 加载所有配置项）
│   ├── provider.py          # LLM 调用封装（OpenAI 兼容客户端）
│   ├── memory.py            # 记忆管理（SQLite 聊天记录 + 会话元数据）
│   ├── personality.py       # AI 人设加载（读取 personality.md）
│   └── chat_service.py      # 聊天业务逻辑（上下文组装、LLM 调用、消息存储）
├── frontend/
│   └── index.html           # 前端单文件 SPA（Vue 3 + Axios + Marked.js）
├── personality.md           # AI 人设定义（名称、性格、对话风格）
├── migrate.py               # 数据迁移脚本，修复早期孤立会话记录
├── data/db/
│   └── assistant_memory.db  # SQLite 数据库
├── requirements.txt         # Python 依赖
└── .env                     # 环境变量（API Key、Base URL 等）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DASHSCOPE_API_KEY=你的百炼API密钥
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

可选配置项（均有默认值）：

```env
CHAT_MODEL=qwen3.5-35b-a3b
CHAT_TEMPERATURE=0.7
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
CORS_ORIGINS=*
DB_PATH=data/db/assistant_memory.db
PERSONALITY_PATH=personality.md
```

### 3. 启动服务

**Web 模式（推荐）：**

```bash
python server.py
```

服务启动后访问 `frontend/index.html` 即可使用聊天界面。API 默认运行在 `http://127.0.0.1:8000`。

**命令行模式：**

```bash
python main.py
```

在终端中直接与 AI 对话，输入 `quit` 退出。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送消息并获取 AI 回复 |
| GET | `/api/history?session_id=xxx` | 获取指定会话的聊天历史 |
| GET | `/api/sessions` | 获取所有会话列表 |
| POST | `/api/sessions/rename` | 重命名会话 |
| DELETE | `/api/sessions/{session_id}` | 删除会话 |

## 功能特性

- 多会话管理：创建、切换、重命名、删除对话
- 聊天记录持久化：基于 SQLite 存储，重启不丢失
- Markdown 渲染：AI 回复支持 Markdown 格式展示
- 可配置人设：通过 `personality.md` 自定义 AI 性格和对话风格
- 模型路由：支持按角色配置不同模型，便于扩展
