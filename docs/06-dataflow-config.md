# 06 · 数据流与配置

[← L4 数据层](05-l4-data.md) | [← 返回目录](README.md) | [下一页：前端与测试 →](07-frontend-testing.md)

---

## 完整请求链路

以一条用户消息从发送到返回为例，完整追踪每一步的调用路径：

```
POST /api/chat  {"message": "帮我写一个排序算法", "session_id": "sess_abc"}
  │
  ▼
routes/chat.py :: chat()
  └── engine.chat("帮我写一个排序算法", "sess_abc")
        │
        ▼
  CognitionEngine.chat()
  └── graph.invoke(initial_state)
        │
        ├─ [节点 1] inject_deps
        │    写入 state: llm, memory, memory_system, guardrail_pipeline
        │
        ├─ [节点 2] guardrail_input
        │    pipeline.check_input("帮我写一个排序算法")
        │    → passed=True，继续
        │
        ├─ [节点 3] memory_retrieve
        │    memory_system.build_system_prompt("sess_abc", "帮我写一个排序算法")
        │    ├── persona.get_system_prompt(user_profile.get_summary())
        │    ├── episodic.get_context_for_prompt("sess_abc")
        │    ├── semantic.get_context_for_prompt("帮我写一个排序算法")
        │    └── skills.get_summary()
        │    → state["context"] = "你是灵曦，..."
        │
        ├─ [节点 4] chat
        │    1. memory_manager.update_session_meta("sess_abc", "帮我写一个排序算法"[:20])
        │    2. memory_manager.add_message("user", "帮我写一个排序算法", "sess_abc")
        │    3. history = memory_manager.get_recent_history(10, "sess_abc")
        │    4. messages = [system_prompt, ...history, user_msg]
        │    5. llm.get_response(messages) → "以下是几种常见排序算法..."
        │    6. memory_manager.add_message("assistant", response, "sess_abc")
        │    7. asyncio.create_task(memory_system.process_conversation(...))
        │    → state["response"] = "以下是几种常见排序算法..."
        │
        └─ [节点 5] guardrail_output
             pipeline.check_output(response, query)
             → passed=True，response 不变
             → final_state["response"] = "以下是几种常见排序算法..."
  │
  ▼
HTTP 200 {"reply": "以下是几种常见排序算法...", "session_id": "sess_abc"}

  （异步，不阻塞响应）
  └── memory_system.process_conversation("sess_abc", messages)
        ├── analyzer.analyze_conversation(messages) → LLM 调用，返回 JSON
        ├── user_profile.update({"technical_skills": ["排序算法"]})
        ├── episodic.add_summary("sess_abc", "讨论了排序算法", ...)
        ├── semantic.add_conversation_knowledge(messages)
        └── skills.register_skill({...}) if new skill detected
```

---

## 输入被拦截的链路

```
POST /api/chat  {"message": "我的密码是 password=abc123", "session_id": "sess_abc"}
  │
  ▼
[节点 2] guardrail_input
  pipeline.check_input("我的密码是 password=abc123")
  → ComplianceGuardrail 匹配到 password= 模式
  → GuardrailResult(passed=False, blocked_reason="检测到密码字段")
  → state["blocked"] = True
  → state["response"] = "[已拦截] 检测到密码字段"
  │
  ▼
条件边 → END（跳过 memory_retrieve、chat、guardrail_output）
  │
  ▼
HTTP 200 {"reply": "[已拦截] 检测到密码字段", "session_id": "sess_abc"}
```

---

## 配置文件说明

### `models.yaml`

```yaml
providers:
  dashscope:
    label: 阿里云百炼
    api_key: ${DASHSCOPE_API_KEY}      # 从环境变量读取
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    models:
      - id: qwen3.6-plus
        label: qwen3.6-plus
      - id: qwen3.5-35b-a3b
        label: qwen3.5-35b-a3b

  mimo:
    label: 小米
    api_key: ${MIMO_API_KEY}
    base_url: https://api.xiaomimimo.com/v1
    models:
      - id: mimo-v2.5-pro
        label: mimo-v2.5-pro

default: dashscope/qwen3.6-plus        # 格式：provider_id/model_id
```

`AppConfig._load_models()` 解析此文件，将 `${VAR}` 替换为 `os.getenv("VAR")`，返回 `(models_dict, default_model_id)`。

`model_config.py` 中的 `MODEL_ROUTING` 目前是硬编码的，与 `models.yaml` 并行存在。**两者需保持同步**，这是当前的一个已知不一致点。

---

### `.env`

```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
MIMO_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

由 `python-dotenv` 在 `server.py` / `main.py` 启动时加载。

---

### `personality.md`

AI 人格的原始定义文件，纯自然语言描述。首次启动时，`PersonaManager.initialize_from_personality_md()` 读取此文件，调用 LLM 解析为结构化 YAML，写入 `persona_manifest.yaml`。

**当前状态**：文件内容为占位符 `"请写入个人助手的人设"`，需要填写实际人设描述才能正确初始化人格。

---

## 数据持久化位置汇总

| 数据类型 | 存储位置 | 格式 | 管理类 |
|---------|---------|------|-------|
| 聊天历史 | `data/db/assistant_memory.db` → `chat_history` | SQLite | MemoryManager |
| Session 元数据 | `data/db/assistant_memory.db` → `sessions` | SQLite | MemoryManager |
| 情景记忆（摘要/任务/事件） | `data/db/assistant_memory.db` → 3 张表 | SQLite | EpisodicMemoryManager |
| 用户画像 | `data/memory/user_profile.json` | JSON | UserProfileManager |
| AI 人格 | `data/memory/persona_manifest.yaml` | YAML | PersonaManager |
| 技能注册表 | `data/memory/skill_registry.json` | JSON | SkillRegistryManager |
| 语义记忆 | `data/memory/chroma/` | ChromaDB | SemanticMemoryManager |

---

## 已知 TODO 与骨架代码

| 位置 | 状态 | 说明 |
|------|------|------|
| `l2_guardrails/factuality.py` | 骨架 | LLM 相关性检查，当前直接放行 |
| `l2_guardrails/alignment.py` | 骨架 | 风格一致性检查，当前直接放行 |
| `l2_guardrails/self_repair.py` | 骨架 | 自我修复重试，当前直接返回原文 |
| `l3_cognition/nodes/tool_node.py` | 骨架 | 工具执行节点，当前透传 state |
| `routes/models.py` → `POST /api/models/switch` | TODO | 运行时切换模型，未实现 |
| `personality.md` | 占位符 | 需填写实际人设描述 |
| `tests/regression/test_personality.py` | 占位符 | 人格一致性回归测试，未实现 |
| `model_config.py` vs `models.yaml` | 不一致 | 两处模型配置需统一 |

---

[← L4 数据层](05-l4-data.md) | [← 返回目录](README.md) | [下一页：前端与测试 →](07-frontend-testing.md)
