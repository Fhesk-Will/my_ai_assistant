# 05 · 关闭与维护

[← 监控面板](04-monitoring.md) | [← 返回目录](README.md)

---

## 正常关闭

### 关闭步骤

1. 关闭浏览器中的助手标签页（或整个浏览器窗口）
2. 切换到运行 `python server.py` 的终端窗口
3. 按 `Ctrl + C`，等待服务停止

终端显示以下内容后，服务已完全停止：

```
INFO:     Shutting down
INFO:     Finished server process [xxxxx]
```

> 直接关闭终端窗口也能停止服务，但建议使用 `Ctrl + C` 以确保数据正确写入。

---

## 数据存储位置

助手的所有数据保存在项目的 `data/` 目录下：

```
data/
├── db/
│   └── assistant_memory.db     # 所有对话记录、情景记忆
└── memory/
    ├── user_profile.json        # 你的用户画像
    ├── persona_manifest.yaml    # AI 人格配置
    ├── skill_registry.json      # 技能注册表
    └── chroma/                  # 语义记忆（向量数据库）
```

---

## 数据备份

### 手动备份

在服务**停止后**，复制整个 `data/` 目录到安全位置即可完成备份。

```
# 示例：复制到桌面备份文件夹
复制 data/ → 桌面/my_ai_assistant_backup_日期/
```

### 恢复备份

将备份的 `data/` 目录覆盖回项目根目录，重新启动服务即可恢复。

> 建议在服务停止状态下进行备份和恢复操作，避免数据不一致。

---

## 常见问题

### 发送消息后长时间没有回复

**可能原因：**
- 网络连接不稳定
- 阿里云百炼服务响应慢或暂时不可用

**处理方法：**
1. 等待约 30 秒，如仍无回复，刷新页面重试
2. 检查网络连接是否正常
3. 查看终端是否有报错信息

---

### 页面显示空白或无法加载

**可能原因：**
- 服务未启动或已意外停止

**处理方法：**
1. 检查终端中 `python server.py` 是否仍在运行
2. 如已停止，重新运行 `python server.py`
3. 刷新浏览器页面

---

### 对话历史消失

**可能原因：**
- 切换了对话，当前显示的是另一个对话
- 误删了对话

**处理方法：**
1. 检查侧边栏对话列表，点击对应对话查看历史
2. 如果对话已被删除，无法恢复（除非有备份）

---

### 助手回复与之前风格不一致

**可能原因：**
- 人格配置文件（`personality.md`）内容为空或未正确填写

**处理方法：**
1. 打开项目根目录的 `personality.md` 文件
2. 填写 AI 助手的人设描述（性格、说话风格、擅长领域等）
3. 删除 `data/memory/persona_manifest.yaml` 文件
4. 重启服务，助手会重新根据 `personality.md` 初始化人格

---

### 终端报错 `DASHSCOPE_API_KEY` 相关错误

**处理方法：**
1. 确认项目根目录存在 `.env` 文件
2. 确认文件内容格式正确：`DASHSCOPE_API_KEY=sk-你的Key`
3. Key 前后无多余空格或引号
4. 重启服务

---

### 想清空所有记忆重新开始

如果你想让助手"忘掉"所有关于你的信息，重新积累：

1. 停止服务（`Ctrl + C`）
2. 删除以下文件（对话记录会保留）：
   - `data/memory/user_profile.json`
   - `data/memory/persona_manifest.yaml`
   - `data/memory/skill_registry.json`
   - `data/memory/chroma/`（整个目录）
3. 重启服务

> 如果同时想清空对话记录，删除 `data/db/assistant_memory.db` 即可。

---

## 更新助手

当项目有新版本时：

1. 停止服务
2. 更新项目文件（通过 git pull 或手动替换）
3. 重新安装依赖：`pip install -r requirements.txt`
4. 重启服务：`python server.py`

数据目录 `data/` 不会被更新覆盖，历史记录和记忆数据会完整保留。

---

[← 监控面板](04-monitoring.md) | [← 返回目录](README.md)
