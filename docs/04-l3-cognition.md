# 04 · L3 认知层

[← L2 护栏层](03-l2-guardrails.md) | [← 返回目录](README.md) | [下一页：L4 数据层 →](05-l4-data.md)

---

## 概述

L3 是系统的"大脑"，负责：
- 封装 LLM 调用（`LLMProvider`）
- 用 LangGraph 定义对话流程（`graph.py`）
- 对外暴露唯一入口（`CognitionEngine`）

---

## CognitionEngine `engine.py`

```python
class CognitionEngine:
    def __init__(self, config, memory_manager, memory_system):
        self.config         = config
        self.memory_manager = memory_manager
        self.memory_system  = memory_system
        self.llm            = LLMProvider(role="chat")
        self.guardrails     = GuardrailPipeline()
        self.graph          = build_graph()   # 编译 LangGraph

    def chat(self, message: str, session_id: str) -> str:
        initial_state = {
            "message": message,
            "session_id": session_id,
            "llm": self.llm,
            "memory": self.memory_manager,
            "memory_system": self.memory_system,
            "guardrail_pipeline": self.guardrails,
        }
        final_state = self.graph.invoke(initial_state)
        return final_state.get("response", "")
```

L1 只持有 `CognitionEngine` 的引用，调用 `chat()` 即可，无需了解内部图结构。

---

## LLM 提供者 `provider.py`

```python
class LLMProvider:
    def __init__(self, role: str = "chat"):
        routing = MODEL_ROUTING[role]          # 从 model_config.py 读取
        self.client = openai.OpenAI(
            api_key  = routing["api_key"],
            base_url = routing["base_url"],
        )
        self.model = routing["model"]

    def get_response(self, messages: list[dict]) -> str:
        resp = self.client.chat.completions.create(
            model    = self.model,
            messages = messages,
        )
        return resp.choices[0].message.content
```

`messages` 格式为标准 OpenAI 消息列表：`[{"role": "system"|"user"|"assistant", "content": "..."}]`。

### 模型路由表 `model_config.py`

```python
MODEL_ROUTING = {
    "chat": {
        "provider": "aliyun_bailian",
        "model":    "qwen3.5-35b-a3b",
        "api_key":  os.getenv("DASHSCOPE_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }
}
```

当前只有 `"chat"` 角色。未来可添加 `"analysis"`、`"embedding"` 等角色，各自使用不同模型。

---

## LangGraph 图 `graph.py`

### 图结构

```
inject_deps
     │
     ▼
guardrail_input ──(blocked)──► END
     │
  (continue)
     │
     ▼
memory_retrieve
     │
     ▼
   chat
     │
     ▼
guardrail_output
     │
     ▼
    END
```

### 节点定义

```python
def build_graph() -> CompiledGraph:
    builder = StateGraph(dict)
    builder.add_node("inject_deps",      inject_deps_node)
    builder.add_node("guardrail_input",  guardrail_input_node)
    builder.add_node("memory_retrieve",  memory_node)
    builder.add_node("chat",             chat_node)
    builder.add_node("guardrail_output", guardrail_output_node)

    builder.set_entry_point("inject_deps")
    builder.add_edge("inject_deps", "guardrail_input")
    builder.add_conditional_edges(
        "guardrail_input",
        lambda s: "blocked" if s.get("blocked") else "continue",
        {"blocked": END, "continue": "memory_retrieve"}
    )
    builder.add_edge("memory_retrieve", "chat")
    builder.add_edge("chat", "guardrail_output")
    builder.add_edge("guardrail_output", END)
    return builder.compile()
```

### State 字段说明

| 字段 | 类型 | 写入节点 | 读取节点 |
|------|------|---------|---------|
| `message` | str | 初始化 | guardrail_input, chat |
| `session_id` | str | 初始化 | memory_retrieve, chat |
| `llm` | LLMProvider | inject_deps | chat |
| `memory` | MemoryManager | inject_deps | chat |
| `memory_system` | MemorySystem | inject_deps | memory_retrieve, chat |
| `guardrail_pipeline` | GuardrailPipeline | inject_deps | guardrail_input, guardrail_output |
| `blocked` | bool | guardrail_input | 条件边 |
| `context` | str | memory_retrieve | chat |
| `response` | str | chat / guardrail_output | engine.chat() 读取 |

---

## 节点实现

### inject_deps 节点

将 `CognitionEngine` 持有的组件写入 state，使后续节点无需直接引用 engine 实例。这是 LangGraph 中实现依赖注入的标准做法。

### guardrail_input 节点

```python
def guardrail_input_node(state: dict) -> dict:
    result = state["guardrail_pipeline"].check_input(state["message"])
    if not result.passed:
        return {**state, "blocked": True, "response": f"[已拦截] {result.blocked_reason}"}
    return {**state, "blocked": False}
```

### memory_node `nodes/memory_node.py`

```python
def memory_node(state: dict) -> dict:
    context = state["memory_system"].build_system_prompt(
        session_id    = state["session_id"],
        current_query = state["message"],
    )
    return {**state, "context": context}
```

`build_system_prompt()` 的实现见 [05 · L4 数据层](05-l4-data.md)。

### chat_node `nodes/chat_node.py`

这是图中最复杂的节点，执行顺序如下：

```
1. 更新 session 元数据
   └── 若为首条消息，截取前 20 字作为 session 标题

2. 将用户消息存入 SQLite（memory_manager.add_message）

3. 构建 system prompt
   └── 优先使用 state["context"]（memory_node 已构建）
   └── 回退：memory_system.build_system_prompt()

4. 从 SQLite 取最近 10 条历史（memory_manager.get_recent_history）

5. 组装 messages 列表
   [system_prompt, ...recent_history, current_user_message]

6. 调用 LLMProvider.get_response(messages)

7. 将 assistant 回复存入 SQLite

8. 异步触发记忆分析
   └── asyncio.create_task(memory_system.process_conversation(...))
   └── 不阻塞当前响应
```

### guardrail_output 节点

```python
def guardrail_output_node(state: dict) -> dict:
    result = state["guardrail_pipeline"].check_output(
        state["response"], query=state["message"]
    )
    if not result.passed and result.sanitized_text:
        return {**state, "response": result.sanitized_text}
    return state
```

### tool_node `nodes/tool_node.py`

当前为骨架，直接透传 state，未来用于执行外部工具调用（API、脚本、数据库查询）。

---

## 上下文管理器 `context_manager.py`

```python
class ContextManager:
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system

    def build_context(self, session_id: str, query: str) -> str:
        return self.memory_system.build_system_prompt(session_id, query)
```

当前是对 `MemorySystem.build_system_prompt()` 的薄封装，预留给未来扩展（如多轮上下文压缩、动态截断）。

---

[← L2 护栏层](03-l2-guardrails.md) | [← 返回目录](README.md) | [下一页：L4 数据层 →](05-l4-data.md)
