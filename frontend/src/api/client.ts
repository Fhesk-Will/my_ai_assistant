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
