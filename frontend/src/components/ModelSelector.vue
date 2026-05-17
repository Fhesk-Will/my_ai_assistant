<template>
  <div class="model-selector">
    <button class="model-btn" @click="toggle" :disabled="loading">
      <span class="model-icon" v-html="modelIcon"></span>
      <span class="model-info">
        <span class="model-name">{{ currentName }}</span>
        <span class="model-provider">{{ currentProvider }}</span>
      </span>
      <svg
        width="12" height="12" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" stroke-width="2.5" stroke-linecap="round"
        :class="{ rotated: open }"
      ><polyline points="6 9 12 15 18 9"/></svg>
    </button>

    <Teleport to="body">
      <div v-if="open" class="dropdown-overlay" @click="open = false" />
      <div v-if="open" class="dropdown-panel">
        <div v-for="group in groupedModels" :key="group.provider" class="dropdown-group">
          <div class="dropdown-group-label">{{ group.provider }}</div>
          <button
            v-for="model in group.items"
            :key="model.id"
            class="dropdown-item"
            :class="{ active: model.id === currentId }"
            @click="selectModel(model)"
          >
            <div class="dropdown-item-main">
              <span class="dropdown-item-name">{{ model.name }}</span>
              <span class="dropdown-item-id">{{ model.id }}</span>
            </div>
            <svg
              v-if="model.id === currentId"
              width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2.5" stroke-linecap="round"
            ><polyline points="20 6 9 17 4 12"/></svg>
          </button>
        </div>
        <div v-if="!loading && models.length === 0" class="dropdown-empty">
          暂无可选模型
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getModels, switchModel, type ModelInfo } from '../api/client'

const models = ref<ModelInfo[]>([])
const currentId = ref('')
const open = ref(false)
const loading = ref(false)

const modelIcon = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`

const currentModel = computed(() => models.value.find(m => m.id === currentId.value))

const currentName = computed(() => currentModel.value?.name || currentId.value || '选择模型')

const currentProvider = computed(() => currentModel.value?.provider || '')

const groupedModels = computed(() => {
  const map = new Map<string, ModelInfo[]>()
  for (const m of models.value) {
    const arr = map.get(m.provider) || []
    arr.push(m)
    map.set(m.provider, arr)
  }
  return Array.from(map.entries()).map(([provider, items]) => ({ provider, items }))
})

function toggle() {
  if (loading.value) return
  open.value = !open.value
}

async function selectModel(model: ModelInfo) {
  if (model.id === currentId.value) {
    open.value = false
    return
  }
  try {
    const res = await switchModel(model.id)
    if (res.status === 'ok') {
      currentId.value = res.current
    }
  } catch (e) {
    console.error('切换模型失败:', e)
  }
  open.value = false
}

async function loadModels() {
  loading.value = true
  try {
    const data = await getModels()
    models.value = data.models
    currentId.value = data.current
  } catch (e) {
    console.error('加载模型列表失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadModels)
</script>

<style scoped>
.model-selector {
  position: relative;
}

.model-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: white;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #374151;
}

.model-btn:hover {
  border-color: #c7d2fe;
  background: #f9fafb;
}

.model-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.model-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: #eef2ff;
  color: #4f46e5;
}

.model-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
}

.model-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
}

.model-provider {
  font-size: 11px;
  color: #9ca3af;
}

.model-btn svg {
  transition: transform 0.2s ease;
}

.model-btn svg.rotated {
  transform: rotate(180deg);
}

.dropdown-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
}

.dropdown-panel {
  position: fixed;
  top: 56px;
  left: 400px;
  z-index: 50;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
  padding: 8px;
  min-width: 260px;
  max-height: 360px;
  overflow-y: auto;
}

.dropdown-group {
  margin-bottom: 4px;
}

.dropdown-group-label {
  padding: 6px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 10px;
  transition: background 0.1s ease;
  text-align: left;
  color: #374151;
}

.dropdown-item:hover {
  background: #f9fafb;
}

.dropdown-item.active {
  background: #eef2ff;
  color: #4f46e5;
}

.dropdown-item-main {
  flex: 1;
}

.dropdown-item-name {
  display: block;
  font-size: 13px;
  font-weight: 500;
}

.dropdown-item-id {
  display: block;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

.dropdown-empty {
  text-align: center;
  padding: 20px;
  color: #9ca3af;
  font-size: 13px;
}
</style>
