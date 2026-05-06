<template>
  <div class="observability-layout">
    <header class="obs-header">
      <router-link to="/" class="back-link">← 返回对话</router-link>
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
          <p class="card-value">{{ summary.recent_errors || 0 }}</p>
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
  padding: 24px;
}

.obs-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.obs-header h1 {
  font-size: 20px;
  color: #e0e0e0;
}

.back-link {
  color: #7aa0d0;
  text-decoration: none;
  font-size: 14px;
}

.back-link:hover {
  color: #9ac0f0;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.card {
  background: #16213e;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
  padding: 20px;
}

.card h3 {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.card-value {
  font-size: 28px;
  font-weight: bold;
  color: #4a90d9;
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 16px;
  color: #a0a0c0;
  margin-bottom: 12px;
}

.memory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.memory-item {
  background: #16213e;
  border: 1px solid #2a2a4a;
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.memory-item .label {
  color: #888;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.metrics-table th,
.metrics-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #2a2a4a;
}

.metrics-table th {
  color: #888;
  font-weight: normal;
  text-transform: uppercase;
  font-size: 11px;
}

.metrics-table td.error {
  color: #ff6b6b;
}

.metrics-table .empty {
  text-align: center;
  color: #666;
  padding: 20px;
}
</style>
