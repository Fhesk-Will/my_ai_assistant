import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface Session {
  id: string
  title: string
  time: string
}

export async function sendMessage(message: string, sessionId: string) {
  const res = await api.post('/chat', { message, session_id: sessionId })
  return res.data.reply as string
}

export async function sendMessageStream(
  message: string,
  sessionId: string,
  onChunk: (content: string) => void,
  onThinking?: (thinking: boolean) => void
): Promise<void> {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') return
      try {
        const parsed = JSON.parse(data)
        if (parsed.error) throw new Error(parsed.error)
        if (parsed.type === 'thinking') {
          onThinking?.(true)
        } else if (parsed.type === 'thinking_done') {
          onThinking?.(false)
        } else if (parsed.content) {
          onChunk(parsed.content)
        }
      } catch (e: any) {
        if (e.message && !e.message.startsWith('Unexpected')) throw e
      }
    }
  }
}

export async function getHistory(sessionId: string) {
  const res = await api.get('/history', { params: { session_id: sessionId } })
  return res.data.history as ChatMessage[]
}

export async function getSessions() {
  const res = await api.get('/sessions')
  return res.data.sessions as Session[]
}

export async function renameSession(sessionId: string, newTitle: string) {
  await api.post('/sessions/rename', { session_id: sessionId, new_title: newTitle })
}

export async function deleteSession(sessionId: string) {
  await api.delete(`/sessions/${sessionId}`)
}

export async function getObservabilityMetrics(limit = 50) {
  const res = await api.get('/observability/metrics', { params: { limit } })
  return res.data.metrics
}

export async function getObservabilitySummary() {
  const res = await api.get('/observability/summary')
  return res.data
}

export async function getMemoryStatus() {
  const res = await api.get('/memory/status')
  return res.data
}

export interface ModelInfo {
  id: string
  name: string
  provider: string
}

export async function getModels(): Promise<{ models: ModelInfo[]; current: string }> {
  const res = await api.get('/models')
  return res.data
}

export async function switchModel(modelId: string): Promise<{ status: string; current: string }> {
  const res = await api.post('/models/switch', { model_id: modelId })
  return res.data
}
