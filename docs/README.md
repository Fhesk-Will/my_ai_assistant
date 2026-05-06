# My AI Assistant — 开发者说明书

> 本说明书面向项目开发者，聚焦架构设计与实现逻辑，不做基础知识讲解。

---

## 目录

| 页面 | 内容 |
|------|------|
| [01 · 架构总览](01-architecture.md) | 四层架构、模块依赖关系、目录结构 |
| [02 · L1 UI 层](02-l1-ui.md) | FastAPI 服务、路由、中间件 |
| [03 · L2 护栏层](03-l2-guardrails.md) | 合规检查、输入输出过滤管道 |
| [04 · L3 认知层](04-l3-cognition.md) | LLM 提供者、LangGraph 编排、节点实现 |
| [05 · L4 数据层](05-l4-data.md) | 五层记忆系统、持久化方案 |
| [06 · 数据流与配置](06-dataflow-config.md) | 完整请求链路、配置文件说明 |
| [07 · 前端与测试](07-frontend-testing.md) | Vue 3 前端结构、测试套件 |

---

## 项目简介

**My AI Assistant** 是一个具备长期记忆的个人 AI 助手，后端使用 Python + FastAPI，前端使用 Vue 3。核心特性：

- **四层分离架构**：UI → 护栏 → 认知 → 数据，职责清晰
- **五层记忆系统**：用户画像、人格管理、情景记忆、语义记忆、技能注册表
- **LangGraph 编排**：对话流程以有向图方式定义，节点可独立扩展
- **LLM 接入**：通过阿里云百炼（DashScope）OpenAI 兼容接口调用 Qwen 系列模型
- **合规护栏**：输入/输出双向敏感信息检测与脱敏

---

## 快速启动

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env   # 填入 DASHSCOPE_API_KEY

# 启动 Web 服务（默认 http://127.0.0.1:8888）
python server.py

# 或使用 CLI 交互模式
python main.py
```

---

## 技术栈一览

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 对话编排 | LangGraph 0.2+ |
| LLM 客户端 | OpenAI SDK（兼容 DashScope） |
| 向量数据库 | ChromaDB 0.4+ |
| 关系数据库 | SQLite |
| 前端 | Vue 3 + Vite + TypeScript |
| 测试 | pytest + pytest-asyncio + httpx |
