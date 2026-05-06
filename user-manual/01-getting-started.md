# 01 · 启动助手

[← 返回目录](README.md) | [下一页：对话界面 →](02-chat-interface.md)

---

## 第一步：准备环境

### 系统要求

- Python 3.10 或更高版本
- 网络连接（用于 LLM 调用）
- 现代浏览器（Chrome、Edge、Firefox 均可）

### 检查 Python 版本

打开终端（命令提示符 / PowerShell / Terminal），输入：

```
python --version
```

输出应为 `Python 3.10.x` 或更高。

---

## 第二步：安装依赖

**首次使用时执行一次**，之后无需重复。

在项目根目录下运行：

```
pip install -r requirements.txt
```

等待安装完成，看到 `Successfully installed ...` 即可。

---

## 第三步：配置 API Key

助手需要通过阿里云百炼服务调用 AI 模型，必须先配置 API Key。

1. 在项目根目录找到 `.env` 文件（如果不存在，新建一个）
2. 用文本编辑器打开，填入你的 API Key：

```
DASHSCOPE_API_KEY=你的Key内容
```

3. 保存文件

> API Key 以 `sk-` 开头，可在阿里云百炼控制台获取。

---

## 第四步：启动服务

在项目根目录下运行：

```
python server.py
```

启动成功后，终端会显示类似以下内容：

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8888 (Press CTRL+C to quit)
```

看到 `Application startup complete` 即表示服务已就绪。

> 启动过程中终端窗口需要保持开启，关闭终端会停止服务。

---

## 第五步：打开助手

打开浏览器，在地址栏输入：

```
http://127.0.0.1:8888
```

按回车，即可看到助手的对话界面。

---

## 首次使用说明

首次启动时，助手会自动完成以下初始化：

- 创建本地数据库（`data/db/assistant_memory.db`）
- 初始化记忆目录（`data/memory/`）
- 读取人格配置文件，生成 AI 人格

这些操作在后台自动完成，无需任何操作。

---

## 常见启动问题

### 端口被占用

如果看到类似 `Address already in use` 的错误，说明 8888 端口已被其他程序占用。

解决方法：关闭占用该端口的程序，或在 `src/l4_data/config.py` 中修改 `server_port` 为其他端口号（如 `8889`），然后重新启动。

### 找不到 API Key

如果启动后发送消息时收到错误，检查 `.env` 文件是否存在且 `DASHSCOPE_API_KEY` 已正确填写（无多余空格）。

### 依赖安装失败

如果 `pip install` 报错，尝试：

```
pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

---

[← 返回目录](README.md) | [下一页：对话界面 →](02-chat-interface.md)
