# 07 · 前端与测试

[← 数据流与配置](06-dataflow-config.md) | [← 返回目录](README.md)

---

## 前端

### 技术栈

| 技术 | 用途 |
|------|------|
| Vue 3 (Composition API) | UI 框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Tauri（可选） | 桌面应用打包（`src-tauri/` 目录存在但未集成） |

### 目录结构

```
frontend/
├── index.html              # SPA 入口，挂载 #app
├── index_legacy.html       # 旧版单文件 HTML（无构建工具版本）
├── vite.config.ts          # Vite 配置，代理 /api → http://127.0.0.1:8888
├── tsconfig.json
├── package.json
├── src/
│   ├── main.ts             # createApp(App).mount('#app')
│   ├── App.vue             # 根组件
│   ├── components/         # UI 组件
│   └── assets/
├── src-tauri/              # Tauri 桌面壳（未集成）
└── dist/                   # Vite 构建产物（FastAPI 静态文件目录）
```

### 开发模式

```bash
cd frontend
npm install
npm run dev     # Vite dev server，默认 http://localhost:5173
                # /api 请求代理到 http://127.0.0.1:8888
```

### 生产构建

```bash
npm run build   # 输出到 frontend/dist/
# FastAPI 自动从 frontend/dist/ 提供静态文件
```

### API 通信

前端通过标准 `fetch` 调用后端 REST API，无 WebSocket。所有请求均为同步请求-响应模式（无流式输出）。

**关键请求：**

```typescript
// 发送消息
POST /api/chat
Body: { message: string, session_id: string }
Response: { reply: string, session_id: string }

// 获取历史
GET /api/history?session_id=xxx&limit=20

// 获取 session 列表
GET /api/sessions
```

### index_legacy.html

`frontend/index_legacy.html` 是早期无构建工具版本，直接通过 CDN 引入 Vue 3，所有逻辑写在单个 HTML 文件中。功能与当前版本基本一致，保留作为备用/参考。

---

## 测试

### 测试结构

```
tests/
├── conftest.py              # 全局 fixtures
├── pytest.ini               # asyncio-mode=auto
├── unit/
│   ├── test_memory.py       # MemoryManager CRUD
│   ├── test_provider.py     # LLMProvider 初始化与 mock
│   └── test_guardrails.py   # ComplianceGuardrail 规则验证
├── integration/
│   ├── test_chat_flow.py    # 完整对话流程（mock LLM）
│   └── test_graph.py        # LangGraph 编译与调用
└── regression/
    └── test_personality.py  # 人格一致性（占位符，未实现）
```

### conftest.py Fixtures

```python
@pytest.fixture
def config() -> AppConfig:
    return AppConfig(db_path=":memory:")   # 内存 SQLite，测试隔离

@pytest.fixture
def memory_manager(config) -> MemoryManager:
    return MemoryManager(config.db_path)

@pytest.fixture
def guardrail_pipeline() -> GuardrailPipeline:
    return GuardrailPipeline()
```

所有测试使用 `:memory:` SQLite，不写磁盘，测试间完全隔离。

---

### 单元测试

#### `test_memory.py` — MemoryManager

覆盖场景：
- `add_message` 后 `get_recent_history` 能取回
- `limit` 参数正确截断
- `update_session_meta` 创建与更新
- `delete_session` 级联删除消息
- `rename_session` 更新 title
- `get_all_sessions` 按时间降序

#### `test_provider.py` — LLMProvider

```python
def test_provider_init(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    provider = LLMProvider(role="chat")
    assert provider.model == "qwen3.5-35b-a3b"

def test_get_response(monkeypatch):
    # mock openai.OpenAI.chat.completions.create
    ...
```

LLM 调用通过 `monkeypatch` mock，不发真实网络请求。

#### `test_guardrails.py` — ComplianceGuardrail

覆盖场景：
- API Key 模式（`sk-` 前缀）被拦截
- 手机号被拦截
- 身份证号被拦截
- 邮箱被拦截
- `password=xxx` 被拦截
- 敏感关键词（身份证、银行卡号）被拦截
- 正常文本通过
- `sanitize_output` 替换而非拦截

---

### 集成测试

#### `test_chat_flow.py` — 完整对话流程

```python
@pytest.mark.asyncio
async def test_full_chat_flow(memory_manager, config, monkeypatch):
    # mock LLMProvider.get_response
    monkeypatch.setattr(LLMProvider, "get_response", lambda self, msgs: "mock reply")

    engine = CognitionEngine(config, memory_manager, MemorySystem(config))
    reply = engine.chat("你好", "test_session")

    assert reply == "mock reply"
    history = memory_manager.get_recent_history(10, "test_session")
    assert len(history) == 2   # user + assistant
```

#### `test_graph.py` — LangGraph

```python
def test_graph_compiles():
    graph = build_graph()
    assert graph is not None

def test_graph_blocked_input(monkeypatch):
    # 输入含敏感信息，验证 blocked=True 且跳过 chat 节点
    ...
```

---

### 运行测试

```bash
# 全部测试
pytest

# 仅单元测试
pytest tests/unit/

# 仅集成测试
pytest tests/integration/

# 详细输出
pytest -v

# 指定测试文件
pytest tests/unit/test_guardrails.py

# 查看覆盖率（需安装 pytest-cov）
pytest --cov=src --cov-report=term-missing
```

`pytest.ini` 配置：

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

---

## CLI 入口 `main.py`

```python
def main():
    config         = AppConfig()
    memory_manager = MemoryManager(config.db_path)
    memory_system  = MemorySystem(config)
    engine         = CognitionEngine(config, memory_manager, memory_system)

    session_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print("AI 助手已启动，输入 'quit' 退出")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        reply = engine.chat(user_input, session_id)
        print(f"助手: {reply}\n")
```

CLI 模式与 Web 模式共用同一套 `CognitionEngine`，数据写入同一个 SQLite 数据库。

---

## 数据迁移 `migrate.py`

修复早期版本产生的孤立 session 问题（有消息记录但无对应 session 元数据行）：

```python
def migrate():
    manager = MemoryManager("data/db/assistant_memory.db")
    orphaned = manager.get_orphaned_sessions()
    for session_id in orphaned:
        # 取该 session 第一条消息的前 20 字作为标题
        history = manager.get_recent_history(1, session_id)
        title = history[0]["content"][:20] if history else "迁移的对话"
        manager.update_session_meta(session_id, title)
    print(f"已修复 {len(orphaned)} 个孤立 session")
```

---

[← 数据流与配置](06-dataflow-config.md) | [← 返回目录](README.md)
