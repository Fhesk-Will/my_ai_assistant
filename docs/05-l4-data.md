# 05 · L4 数据层

[← L3 认知层](04-l3-cognition.md) | [← 返回目录](README.md) | [下一页：数据流与配置 →](06-dataflow-config.md)

---

## 概述

L4 是系统的持久化层，包含两个独立模块：
- **MemoryManager**：SQLite 聊天历史与 session 管理
- **MemorySystem**：五层长期记忆系统的门面类

两者都由 `CognitionEngine` 持有，通过 LangGraph state 传入节点。

---

## 配置 `config.py`

```python
@dataclass
class AppConfig:
    db_path:               str  = "data/db/assistant_memory.db"
    personality_path:      str  = "personality.md"
    memory_dir:            str  = "data/memory"
    chroma_path:           str  = "data/memory/chroma"
    analysis_batch_size:   int  = 5      # 每 N 条消息触发一次分析
    memory_retrieval_limit: int = 5      # 语义检索返回条数
    server_host:           str  = "127.0.0.1"
    server_port:           int  = 8888
    cors_origins:          list = field(default_factory=lambda: ["*"])
    models:                dict = field(default_factory=dict)
    default_model_id:      str  = ""
```

`models` 和 `default_model_id` 由 `_load_models("models.yaml")` 填充，支持 `${ENV_VAR}` 语法解析环境变量。

---

## MemoryManager `memory_store.py`

SQLite 封装，管理聊天历史和 session 元数据。

### 表结构

```sql
CREATE TABLE chat_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,          -- 'user' | 'assistant'
    content     TEXT NOT NULL,
    media_paths TEXT DEFAULT '[]',      -- JSON 数组，预留多模态
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_embedded INTEGER DEFAULT 0       -- 是否已向量化
);

CREATE TABLE sessions (
    session_id  TEXT PRIMARY KEY,
    title       TEXT DEFAULT '新对话',
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 主要方法

| 方法 | 说明 |
|------|------|
| `add_message(role, content, session_id, media_paths)` | 写入一条消息 |
| `get_recent_history(limit, session_id)` | 取最近 N 条，返回 `[{"role":..., "content":...}]` |
| `get_all_sessions()` | 列出所有 session，按 `updated_at` 降序 |
| `update_session_meta(session_id, title)` | INSERT OR REPLACE session 记录 |
| `delete_session(session_id)` | 级联删除 session 及其所有消息 |
| `rename_session(session_id, new_title)` | 更新 title 字段 |
| `get_orphaned_sessions()` | 查找有消息但无 session 记录的孤立数据（迁移用） |

---

## MemorySystem `memory/memory_system.py`

五层记忆的门面类，对外提供两个核心方法：

```python
class MemorySystem:
    def build_system_prompt(self, session_id: str, current_query: str) -> str:
        # 聚合所有记忆层的上下文，返回完整 system prompt

    async def process_conversation(self, session_id: str, messages: list[dict]):
        # 异步分析对话，更新各记忆层
```

内部持有五个子管理器：

```python
self.analyzer     = MemoryAnalyzer(config)
self.user_profile = UserProfileManager(config.memory_dir)
self.persona      = PersonaManager(config.memory_dir, config.personality_path)
self.episodic     = EpisodicMemoryManager(config.db_path)
self.semantic     = SemanticMemoryManager(config.chroma_path)
self.skills       = SkillRegistryManager(config.memory_dir)
```

### build_system_prompt 组装逻辑

```
1. persona.get_system_prompt(user_profile_summary)
   → 人格定义 + 用户画像摘要

2. episodic.get_context_for_prompt(session_id)
   → 最近 N 条 session 摘要 + 活跃任务 + 关键事件

3. semantic.get_context_for_prompt(current_query)
   → 向量检索相关知识片段

4. skills.get_summary()
   → 已注册技能列表

拼接为完整 system prompt 字符串返回
```

### process_conversation 分析流程

```
1. analyzer.analyze_conversation(messages)
   → 调用 LLM，返回结构化 JSON

2. 并行更新各层：
   user_profile.update(analysis["user_facts"])
   episodic.add_summary(session_id, analysis["session_summary"], ...)
   episodic.add_task(...)  for each task
   episodic.add_event(...) for each key_event
   semantic.add_conversation_knowledge(messages)
   skills.register_skill(...) for each new skill
   persona.adjust(analysis["persona_adjustments"])
```

---

## 五层记忆详解

### 层 1：用户画像 `user_profile.py`

**持久化**：`data/memory/user_profile.json`

```json
{
  "basic": {
    "name": null,
    "occupation": null,
    "location": null,
    "language_preference": "zh-CN"
  },
  "interests": [],
  "technical_skills": [],
  "communication_preferences": {
    "verbosity": "medium",
    "formality": "semi-formal",
    "emoji_tolerance": "low"
  },
  "interaction_stats": {
    "total_sessions": 0,
    "total_messages": 0,
    "first_interaction": null,
    "last_interaction": null
  }
}
```

`update(new_facts)` 做深度合并：列表字段追加去重，标量字段覆盖，`fact_N` 键直接写入。

`get_summary()` 将画像格式化为自然语言段落，注入 system prompt。

---

### 层 2：人格管理 `persona.py`

**持久化**：`data/memory/persona_manifest.yaml`

```yaml
version: 2
name: 灵曦
base_personality: 温暖、耐心、富有好奇心
tone:
  default: 温柔专业
  technical: 准确严谨
  casual: 轻松幽默
rules:
  - 始终以用户需求为中心
  - 回答要简洁清晰，避免冗余
  - ...
evolution_log:
  - timestamp: "2026-05-01T..."
    change: "调整语气为更温柔专业"
    reason: "用户反馈"
base_from_md: "..."   # personality.md 的原始内容
```

**初始化流程**：首次运行时，`initialize_from_personality_md()` 读取 `personality.md`，调用 LLM 解析为结构化 YAML，写入 `persona_manifest.yaml`。

`adjust(adjustments)` 接收分析器提取的调整建议，修改 `tone`/`rules`，并在 `evolution_log` 中追加记录。

`get_system_prompt(user_profile_summary)` 将人格配置格式化为 system prompt 的开头部分。

---

### 层 3：情景记忆 `episodic.py`

**持久化**：SQLite（与聊天历史同一数据库）

```sql
CREATE TABLE session_summaries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    summary     TEXT,
    topics      TEXT,   -- JSON 数组
    key_events  TEXT,   -- JSON 数组
    mood        TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE task_states (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT,
    task_description TEXT,
    status           TEXT DEFAULT 'pending',  -- pending|in_progress|done
    context          TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE key_events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type       TEXT,
    description      TEXT,
    source_session_id TEXT,
    event_date       TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

`get_context_for_prompt(session_id, limit=3)` 返回格式化字符串，包含最近摘要、活跃任务、近期事件。

---

### 层 4：语义记忆 `semantic.py`

**持久化**：ChromaDB（`data/memory/chroma/`）

**Collections：**

| Collection | 存储内容 |
|-----------|---------|
| `user_knowledge` | 用户提及的技术知识、领域信息 |
| `conversation_facts` | 对话中出现的事实性信息 |

```python
def add_memory(self, text: str, metadata: dict, collection: str, memory_id: str = None):
    col = self.client.get_or_create_collection(collection)
    col.add(documents=[text], metadatas=[metadata], ids=[memory_id or uuid4()])

def search(self, query: str, n_results: int = 5, collection: str = "user_knowledge",
           filter_dict: dict = None) -> list[dict]:
    col = self.client.get_collection(collection)
    results = col.query(query_texts=[query], n_results=n_results, where=filter_dict)
    return results["documents"][0]
```

`add_conversation_knowledge(messages)` 从消息列表中提取知识片段（当前实现：将 assistant 消息直接存入 `conversation_facts`）。

`get_context_for_prompt(query, limit)` 在两个 collection 中各搜索，合并去重后返回格式化字符串。

---

### 层 5：技能注册表 `skill_registry.py`

**持久化**：`data/memory/skill_registry.json`

```json
[
  {
    "id": "skill_abc123",
    "name": "LangGraph状态流与节点路由设计",
    "description": "...",
    "trigger_patterns": ["langgraph", "状态图", "节点路由"],
    "tool_type": "query",
    "proficiency": 0.5,
    "verified": false,
    "usage_count": 0,
    "created_at": "2026-05-01T...",
    "last_used": null
  }
]
```

`find_skill(query)` 做模糊匹配：先精确匹配 `name`，再检查 `trigger_patterns` 是否包含 query 中的关键词。

`verify_skill(skill_id)` 将 `verified` 置为 `true`，`proficiency` 提升 0.1（上限 1.0）。

---

## 记忆分析器 `analyzer.py`

分析器是记忆系统的"写入引擎"，通过 LLM 从对话中提取结构化信息。

### Prompt 结构

```
系统：你是一个对话分析助手，请从以下对话中提取结构化信息，以 JSON 格式返回。

对话内容：
[user]: ...
[assistant]: ...

请返回以下 JSON 结构：
{
  "user_facts": {
    "name": null,
    "occupation": null,
    "interests": [],
    "technical_skills": [],
    "other_facts": []
  },
  "session_summary": "一句话摘要",
  "topics": ["话题1", "话题2"],
  "key_events": [{"type": "...", "description": "...", "date": "..."}],
  "tasks": [{"description": "...", "status": "pending|in_progress|done"}],
  "skills": [{"name": "...", "description": "...", "trigger_patterns": [], "tool_type": "..."}],
  "persona_adjustments": {"tone": null, "rules_to_add": [], "rules_to_remove": []}
}
```

### 响应解析

`_parse_response(response)` 处理 LLM 返回的 markdown 代码块：
1. 尝试提取 ` ```json ... ``` ` 块
2. 回退：直接 `json.loads(response)`
3. 失败：返回空结构，不抛异常

### 触发时机

`chat_node` 在存储 assistant 回复后，通过 `asyncio.create_task()` 异步触发 `process_conversation()`，每 `analysis_batch_size`（默认 5）条消息分析一次。

---

[← L3 认知层](04-l3-cognition.md) | [← 返回目录](README.md) | [下一页：数据流与配置 →](06-dataflow-config.md)
