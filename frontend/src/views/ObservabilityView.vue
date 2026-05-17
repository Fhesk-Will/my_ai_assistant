<template>
  <div class="observability-layout">
    <header class="obs-header">
      <button class="back-link" @click="$router.push('/')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        返回对话
      </button>
      <h1>可观测性监控面板</h1>
    </header>

    <div class="obs-content">
      <!-- 概览卡片 -->
      <section class="cards">
        <div class="card">
          <h3>总请求数</h3>
          <p class="card-value">{{ summary.total_requests || 0 }}</p>
        </div>
        <div class="card">
          <h3>平均响应时间</h3>
          <p class="card-value">{{ summary.avg_duration_ms || 0 }} ms</p>
        </div>
        <div class="card">
          <h3>近期错误</h3>
          <p class="card-value error">{{ summary.recent_errors || 0 }}</p>
        </div>
        <div class="card">
          <h3>记忆状态</h3>
          <p class="card-value">{{ memoryStatus?.semantic?.available ? '正常' : '离线' }}</p>
        </div>
      </section>

      <!-- 记忆系统状态 -->
      <section class="section" v-if="memoryStatus">
        <h2>记忆系统</h2>
        <div class="memory-grid">
          <div class="memory-item">
            <span class="label">用户画像</span>
            <span>兴趣 {{ memoryStatus.user_profile?.interests_count || 0 }} 项 / 技能 {{ memoryStatus.user_profile?.skills_count || 0 }} 项</span>
          </div>
          <div class="memory-item">
            <span class="label">人格版本</span>
            <span>{{ memoryStatus.persona?.name }} v{{ memoryStatus.persona?.version || 1 }}</span>
          </div>
          <div class="memory-item">
            <span class="label">情景记忆</span>
            <span>摘要 {{ memoryStatus.episodic?.summaries_count || 0 }} / 任务 {{ memoryStatus.episodic?.active_tasks_count || 0 }} / 事件 {{ memoryStatus.episodic?.events_count || 0 }}</span>
          </div>
          <div class="memory-item">
            <span class="label">语义记忆</span>
            <span>知识 {{ memoryStatus.semantic?.knowledge_count || 0 }} / 事实 {{ memoryStatus.semantic?.facts_count || 0 }}</span>
          </div>
          <div class="memory-item">
            <span class="label">技能</span>
            <span>总计 {{ memoryStatus.skills?.total_count || 0 }} / 已验证 {{ memoryStatus.skills?.verified_count || 0 }}</span>
          </div>
        </div>
      </section>

      <!-- 最近请求 -->
      <section class="section">
        <h2>最近请求</h2>
        <table class="metrics-table">
          <thead>
            <tr>
              <th>路径</th>
              <th>方法</th>
              <th>状态码</th>
              <th>耗时(ms)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(m, idx) in metrics" :key="idx">
              <td>{{ m.path }}</td>
              <td>{{ m.method }}</td>
              <td :class="{ error: m.status_code >= 400 }">{{ m.status_code }}</td>
              <td>{{ m.duration_ms }}</td>
            </tr>
            <tr v-if="metrics.length === 0">
              <td colspan="4" class="empty">暂无数据</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getObservabilityMetrics, getObservabilitySummary, getMemoryStatus } from '../api/client'

const summary = ref<any>({})
const metrics = ref<any[]>([])
const memoryStatus = ref<any>(null)

async function loadData() {
  try {
    const [s, m, mem] = await Promise.all([
      getObservabilitySummary(),
      getObservabilityMetrics(20),
      getMemoryStatus(),
    ])
    summary.value = s
    metrics.value = m
    memoryStatus.value = mem
  } catch (err) {
    console.error('加载监控数据失败:', err)
  }
}

onMounted(loadData)
</script>

<style scoped>
.observability-layout {
  width: 100%;
  height: 100vh;
  overflow-y: auto;
  padding: 32px;
  background: #fafafa;
}

.obs-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.obs-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #6366f1;
  cursor: pointer;
  font-size: 14px;
  padding: 6px 12px;
  border-radius: 8px;
  transition: background 0.15s ease;
}

.back-link:hover {
  background: #eef2ff;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.card {
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card h3 {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
  font-weight: 500;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #6366f1;
}

.card-value.error {
  color: #ef4444;
}

.section {
  margin-bottom: 36px;
}

.section h2 {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 14px;
}

.memory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.memory-item {
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  padding: 14px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #374151;
}

.memory-item .label {
  color: #9ca3af;
  font-weight: 500;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #f3f4f6;
}

.metrics-table th,
.metrics-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f3f4f6;
}

.metrics-table th {
  color: #9ca3af;
  font-weight: 500;
  font-size: 11px;
  background: #fafafa;
}

.metrics-table td {
  color: #374151;
}

.metrics-table td.error {
  color: #ef4444;
  font-weight: 600;
}

.metrics-table .empty {
  text-align: center;
  color: #9ca3af;
  padding: 24px;
}
</style>
