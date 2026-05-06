# 01 · 架构总览

[← 返回目录](README.md) | [下一页：L1 UI 层 →](02-l1-ui.md)

---

## 四层架构

```
┌──────────────────────────────────────────────────────────────┐
│  L1  UI 层          src/l1_ui/                               │
│  FastAPI 服务 · 路由注册 · 中间件 · 静态文件                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ CognitionEngine.chat()
┌────────────────────────────▼─────────────────────────────────┐
│  L2  护栏层         src/l2_guardrails/                        │
│  输入合规检查 · 输出脱敏 · 可扩展管道                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ GuardrailPipeline
┌────────────────────────────▼─────────────────────────────────┐
│  L3  认知层         src/l3_cognition/                         │
│  LangGraph 编排 · LLM 调用 · 上下文构建                       │
└────────────────────────────┬─────────────────────────────────┘
                             │ MemorySystem / MemoryManager
┌────────────────────────────▼─────────────────────────────────┐
│  L4  数据层         src/l4_data/                              │
│  五层记忆 · SQLite · ChromaDB · JSON/YAML 持久化              │
└──────────────────────────────────────────────────────────────┘
```

每层只向下依赖，不向上引用。L3 持有 L4 的实例，L2 被 L3 的图节点调用，L1 持有 L3 的 `CognitionEngine`。

---

## 目录结构

```
my_ai_assistant/
├── server.py               # Web 服务入口（调用 src/l1_ui/server.py）
├── main.py                 # CLI REPL 入口
├── migrate.py              # 数据迁移脚本（修复孤立 session）
├── models.yaml             # LLM 提供者与模型配置
├── personality.md          # AI 人设原始定义（人格初始化来源）
├── requirements.txt
├── pytest.ini
├── .env                    # DASHSCOPE_API_KEY / MIMO_API_KEY
│
├── src/
│   ├── l1_ui/
│   │   ├── server.py       # create_app() 工厂函数
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── memory.py
│   │   │   ├── models.py
│   │   │   └── observability.py
│   │   └── middleware/
│   │       └── metrics.py
│   │
│   ├── l2_guardrails/
│   │   ├── pipeline.py     # GuardrailPipeline 组合器
│   │   ├── compliance.py   # 敏感信息检测（已实现）
│   │   ├── factuality.py   # 相关性检查（骨架）
│   │   ├── alignment.py    # 风格一致性（骨架）
│   │   └── self_repair.py  # 自我修复（骨架）
│   │
│   ├── l3_cognition/
│   │   ├── engine.py       # CognitionEngine（对外唯一入口）
│   │   ├── graph.py        # LangGraph 图定义与编译
│   │   ├── provider.py     # LLMProvider（OpenAI 客户端封装）
│   │   ├── model_config.py # MODEL_ROUTING 路由表
│   │   ├── context_manager.py
│   │   └── nodes/
│   │       ├── chat_node.py
│   │       ├── memory_node.py
│   │       └── tool_node.py
│   │
│   └── l4_data/
│       ├── config.py       # AppConfig dataclass
│       ├── memory_store.py # MemoryManager（SQLite 聊天历史）
│       └── memory/
│           ├── memory_system.py   # MemorySystem 门面类
│           ├── analyzer.py        # LLM 驱动的对话分析器
│           ├── user_profile.py    # 用户画像（JSON）
│           ├── persona.py         # AI 人格（YAML）
│           ├── episodic.py        # 情景记忆（SQLite）
│           ├── semantic.py        # 语义记忆（ChromaDB）
│           └── skill_registry.py  # 技能注册表（JSON）
│
├── data/
│   ├── db/
│   │   └── assistant_memory.db   # SQLite 主数据库
│   └── memory/
│       ├── user_profile.json
│       ├── persona_manifest.yaml
│       ├── skill_registry.json
│       └── chroma/               # ChromaDB 持久化目录
│
├── frontend/
│   ├── src/                      # Vue 3 源码
│   ├── dist/                     # Vite 构建产物（服务器静态文件目录）
│   └── index.html
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── regression/
│
└── docs/                         # 本说明书
```

---

## 模块依赖关系

```
server.py (入口)
  └── src/l1_ui/server.py
        ├── routes/chat.py
        │     └── src/l3_cognition/engine.py (CognitionEngine)
        │           ├── src/l3_cognition/graph.py (LangGraph)
        │           │     ├── nodes/chat_node.py
        │           │     │     ├── src/l4_data/memory_store.py
        │           │     │     └── src/l3_cognition/provider.py
        │           │     ├── nodes/memory_node.py
        │           │     │     └── src/l4_data/memory/memory_system.py
        │           │     └── src/l2_guardrails/pipeline.py
        │           └── src/l4_data/config.py
        ├── routes/memory.py
        │     └── src/l4_data/memory/memory_system.py
        └── middleware/metrics.py
```

---

## 关键设计决策

### 1. LangGraph 作为对话编排器
对话流程不是简单的函数调用链，而是一个有向图。这使得未来可以在图中插入新节点（如工具调用、多轮规划）而不修改现有节点。

### 2. 记忆系统与对话引擎解耦
`MemorySystem` 通过 LangGraph state 注入到节点，而非硬编码依赖。记忆分析（`process_conversation`）在后台异步执行，不阻塞响应。

### 3. 护栏作为独立管道
`GuardrailPipeline` 是可组合的检查器列表，每个检查器独立实现 `check()` 接口。当前只有 `ComplianceGuardrail` 完整实现，其余为骨架，可按需填充。

### 4. 配置与代码分离
LLM 提供者、模型 ID、API Key 全部在 `models.yaml` + `.env` 中定义，代码中通过 `AppConfig` 读取，不硬编码。

---

[← 返回目录](README.md) | [下一页：L1 UI 层 →](02-l1-ui.md)
