<template>
  <div class="chat-layout">
    <Sidebar
      :sessions="sessions"
      :activeId="currentSessionId"
      @select="switchSession"
      @rename="handleRename"
      @delete="handleDelete"
      @newChat="createNewSession"
    />

    <div class="chat-main" :class="{ empty: messages.length === 0 && !loading }">
      <!-- Top bar -->
      <header class="chat-topbar">
        <div class="topbar-left">
          <ModelSelector />
        </div>
        <div class="topbar-center">
          <span class="session-label">{{ currentSession?.title || '新对话' }}</span>
        </div>
        <div class="topbar-right" />
      </header>

      <!-- Messages area -->
      <div class="messages" ref="messagesRef" v-if="messages.length > 0 || loading">
        <TransitionGroup name="msg">
          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            class="message-row"
            :class="msg.role"
          >
            <!-- AI avatar -->
            <div v-if="msg.role === 'assistant'" class="msg-avatar">
              <div class="avatar-ai">AI</div>
            </div>

            <div class="msg-body">
              <div class="msg-bubble" :class="msg.role">
                <div class="msg-content" v-html="renderMarkdown(msg.content)"></div>
              </div>
              <div v-if="msg.content && !loading" class="msg-meta" :class="msg.role">
                <span class="msg-time">{{ formatTime(msg.timestamp) }}</span>
                <template v-if="msg.role === 'assistant'">
                  <button class="msg-action" title="复制" @click="copyContent(msg.content)">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                  </button>
                  <button class="msg-action" title="重新生成" @click="retryLastMessage">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
                  </button>
                  <button class="msg-action" title="赞同">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                  </button>
                  <button class="msg-action" title="不赞同">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>
                  </button>
                </template>
              </div>
            </div>

            <!-- User avatar -->
            <div v-if="msg.role === 'user'" class="msg-avatar">
              <div class="avatar-user">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
            </div>
          </div>
        </TransitionGroup>

        <!-- Typing indicator -->
        <div v-if="loading && thinking" class="message-row assistant">
          <div class="msg-avatar">
            <div class="avatar-ai">AI</div>
          </div>
          <div class="msg-body">
            <div class="msg-bubble thinking">
              <span class="thinking-text">AI 正在思考</span>
              <span class="thinking-dots">
                <span class="dot" :style="{ animationDelay: '0s' }"></span>
                <span class="dot" :style="{ animationDelay: '0.15s' }"></span>
                <span class="dot" :style="{ animationDelay: '0.3s' }"></span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="empty-state">
        <div class="empty-icon">AI</div>
        <h1 class="empty-heading">有什么可以帮助你的？</h1>
        <div class="suggestions">
          <button
            v-for="s in suggestions"
            :key="s"
            class="suggestion-btn"
            @click="fillSuggestion(s)"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- Input area -->
      <div class="input-area">
        <div class="input-box">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            @keydown.enter.exact="handleSend"
            @compositionstart="composing = true"
            @compositionend="composing = false"
            placeholder="输入消息… (Enter 发送，Shift+Enter 换行)"
            rows="1"
          ></textarea>
          <div class="input-footer">
            <span class="char-count">{{ inputText.length > 0 ? inputText.length + ' 字' : '' }}</span>
            <button
              class="btn-send"
              :class="{ active: inputText.trim() }"
              @click="handleSend"
              :disabled="loading || !inputText.trim()"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { sendMessageStream, getHistory, getSessions, renameSession, deleteSession, type ChatMessage, type Session } from '../api/client'
import Sidebar from '../components/Sidebar.vue'
import ModelSelector from '../components/ModelSelector.vue'

const sessions = ref<Session[]>([])
const messages = ref<(ChatMessage & { timestamp?: string })[]>([])
const currentSessionId = ref('default_session')
const inputText = ref('')
const loading = ref(false)
const thinking = ref(false)
const composing = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const suggestions = [
  '帮我写一篇关于人工智能的文章',
  '解释一下量子计算的基本原理',
  '用 Python 实现一个快速排序算法',
  '给我推荐几本科幻小说',
]

const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value)
})

function fillSuggestion(text: string) {
  inputText.value = text
  textareaRef.value?.focus()
}

function formatTime(ts?: string) {
  if (!ts) {
    return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return ts
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

async function copyContent(text: string) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
}

async function retryLastMessage() {
  if (messages.value.length < 2) return
  const lastUser = messages.value[messages.value.length - 2]
  if (lastUser.role !== 'user') return
  messages.value = messages.value.slice(0, -2)
  inputText.value = lastUser.content
  await handleSend()
}

function generateSessionId(): string {
  return 'session_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
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

async function handleRename(sessionId: string, newTitle: string) {
  try {
    await renameSession(sessionId, newTitle)
    await loadSessions()
  } catch {}
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
  if (composing.value) return

  e?.preventDefault()
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  messages.value.push({ role: 'user', content: text, timestamp: now })
  await scrollToBottom()

  loading.value = true
  thinking.value = true
  messages.value.push({ role: 'assistant', content: '', timestamp: now })
  const assistantIdx = messages.value.length - 1

  try {
    await sendMessageStream(text, currentSessionId.value, (chunk) => {
      messages.value[assistantIdx].content += chunk
      messages.value[assistantIdx].timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      scrollToBottom()
    }, (isThinking) => {
      thinking.value = isThinking
    })
    await loadSessions()
  } catch (err: any) {
    if (!messages.value[assistantIdx].content) {
      messages.value[assistantIdx].content = `错误: ${err.message || '请求失败'}`
    }
  } finally {
    loading.value = false
    thinking.value = false
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

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  overflow: hidden;
}

.chat-main.empty {
  background: #fafafa;
}

/* ── Top bar ── */
.chat-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #f3f4f6;
}

.topbar-left {
  flex-shrink: 0;
}

.topbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.session-label {
  font-size: 13px;
  color: #9ca3af;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.topbar-right {
  flex-shrink: 0;
}

/* ── Messages ── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px 100px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 32px;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.msg-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.avatar-ai {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.3);
}

.avatar-user {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
}

.msg-body {
  max-width: 75%;
  min-width: 0;
}

.msg-bubble {
  padding: 14px 20px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.msg-bubble.user {
  background: #6366f1;
  color: white;
  border-radius: 16px 16px 4px 16px;
}

.msg-bubble.assistant {
  background: white;
  color: #374151;
  border: 1px solid #f3f4f6;
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.msg-bubble.thinking {
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 16px 16px 16px 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.thinking-text {
  color: #9ca3af;
  font-size: 13px;
}

.thinking-dots {
  display: flex;
  gap: 3px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #a5b4fc;
  animation: bounce 1.4s infinite ease-in-out both;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  padding: 0 4px;
}

.msg-meta.user {
  justify-content: flex-end;
}

.msg-meta.assistant {
  justify-content: flex-start;
}

.msg-time {
  font-size: 11px;
  color: #bbb;
  margin-right: 8px;
}

.msg-action {
  padding: 6px;
  border-radius: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  color: #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s ease;
}

.msg-action:hover {
  color: #6366f1;
}

/* ── Message content styles ── */
.msg-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.msg-bubble.user .msg-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.msg-content :deep(strong) {
  font-weight: 600;
}

/* ── Empty state ── */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 100px;
}

.empty-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.25);
  margin-bottom: 20px;
}

.empty-heading {
  font-size: 22px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  max-width: 520px;
}

.suggestion-btn {
  text-align: left;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: white;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
  transition: all 0.15s ease;
}

.suggestion-btn:hover {
  border-color: #a5b4fc;
  color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.06);
}

/* ── Input area ── */
.input-area {
  flex-shrink: 0;
  padding: 12px 100px 24px;
}

.input-box {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: border-color 0.15s ease;
  overflow: hidden;
}

.input-box:focus-within {
  border-color: #a5b4fc;
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.06);
}

.input-box textarea {
  width: 100%;
  padding: 16px 20px 8px;
  border: none;
  background: transparent;
  color: #1f2937;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  min-height: 52px;
  max-height: 200px;
}

.input-box textarea::placeholder {
  color: #d1d5db;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 16px 12px;
}

.char-count {
  font-size: 11px;
  color: #d1d5db;
}

.btn-send {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  border: none;
  background: #f3f4f6;
  color: #d1d5db;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.btn-send.active {
  background: #6366f1;
  color: white;
}

.btn-send.active:hover {
  background: #4f46e5;
}

.btn-send:disabled {
  cursor: not-allowed;
}

/* ── Transition ── */
.msg-enter-active {
  transition: all 0.3s ease-out;
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.msg-leave-active {
  transition: all 0.2s ease-in;
}

.msg-leave-to {
  opacity: 0;
}
</style>
