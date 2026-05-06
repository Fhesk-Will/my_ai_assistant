<template>
  <div class="chat-layout">
    <!-- 侧边栏：会话列表 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>对话列表</h2>
        <button class="btn-new" @click="createNewSession">+ 新对话</button>
      </div>
      <div class="session-list">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === currentSessionId }"
          @click="switchSession(session.id)"
        >
          <span class="session-title">{{ session.title }}</span>
          <span class="session-time">{{ session.time }}</span>
          <button class="btn-delete" @click.stop="handleDelete(session.id)">×</button>
        </div>
      </div>
      <div class="sidebar-footer">
        <router-link to="/observability" class="nav-link">监控面板</router-link>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <div class="messages" ref="messagesRef">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div class="message-bubble">
            <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
        <div v-if="loading" class="message assistant">
          <div class="message-bubble">
            <span class="typing-indicator">思考中...</span>
          </div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputText"
          @keydown.enter.exact="handleSend"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          rows="1"
        ></textarea>
        <button class="btn-send" @click="handleSend" :disabled="loading || !inputText.trim()">
          发送
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { sendMessage, getHistory, getSessions, deleteSession, type ChatMessage, type Session } from '../api/client'

const sessions = ref<Session[]>([])
const messages = ref<ChatMessage[]>([])
const currentSessionId = ref('default_session')
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref<HTMLElement | null>(null)

function generateSessionId(): string {
  return 'session_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

async function loadSessions() {
  sessions.value = await getSessions()
}

async function loadHistory(sessionId: string) {
  messages.value = await getHistory(sessionId)
  await scrollToBottom()
}

async function switchSession(sessionId: string) {
  currentSessionId.value = sessionId
  await loadHistory(sessionId)
}

function createNewSession() {
  const newId = generateSessionId()
  currentSessionId.value = newId
  messages.value = []
}

async function handleDelete(sessionId: string) {
  await deleteSession(sessionId)
  await loadSessions()
  if (sessionId === currentSessionId.value) {
    createNewSession()
  }
}

async function handleSend(e?: Event) {
  if (e && (e as KeyboardEvent).shiftKey) return

  e?.preventDefault()
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  messages.value.push({ role: 'user', content: text })
  await scrollToBottom()

  loading.value = true
  try {
    const reply = await sendMessage(text, currentSessionId.value)
    messages.value.push({ role: 'assistant', content: reply })
    await loadSessions()
  } catch (err: any) {
    messages.value.push({ role: 'assistant', content: `错误: ${err.message || '请求失败'}` })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onMounted(async () => {
  await loadSessions()
  if (sessions.value.length > 0) {
    currentSessionId.value = sessions.value[0].id
    await loadHistory(currentSessionId.value)
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  width: 100%;
  height: 100vh;
}

.sidebar {
  width: 260px;
  background: #16213e;
  border-right: 1px solid #2a2a4a;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #2a2a4a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  font-size: 14px;
  color: #a0a0c0;
}

.btn-new {
  background: #4a90d9;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}

.btn-new:hover {
  background: #5aa0e9;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.session-item:hover {
  background: #1f3460;
}

.session-item.active {
  background: #2a4a7a;
}

.session-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 11px;
  color: #666;
  margin-top: 2px;
}

.btn-delete {
  position: absolute;
  right: 8px;
  top: 8px;
  background: none;
  border: none;
  color: #888;
  font-size: 16px;
  cursor: pointer;
  display: none;
}

.session-item:hover .btn-delete {
  display: block;
}

.btn-delete:hover {
  color: #ff6b6b;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #2a2a4a;
}

.nav-link {
  color: #7aa0d0;
  text-decoration: none;
  font-size: 13px;
}

.nav-link:hover {
  color: #9ac0f0;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.message.user .message-bubble {
  background: #4a90d9;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: #2a2a4a;
  color: #e0e0e0;
  border-bottom-left-radius: 4px;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.typing-indicator {
  color: #888;
  font-style: italic;
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid #2a2a4a;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-area textarea {
  flex: 1;
  background: #2a2a4a;
  border: 1px solid #3a3a5a;
  border-radius: 12px;
  padding: 12px 16px;
  color: #e0e0e0;
  font-size: 14px;
  resize: none;
  outline: none;
  min-height: 44px;
  max-height: 120px;
  font-family: inherit;
}

.input-area textarea:focus {
  border-color: #4a90d9;
}

.btn-send {
  background: #4a90d9;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.btn-send:hover:not(:disabled) {
  background: #5aa0e9;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
