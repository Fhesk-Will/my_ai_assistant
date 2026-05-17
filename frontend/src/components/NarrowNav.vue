<template>
  <nav class="narrow-nav">
    <div class="nav-logo">
      <div class="logo-box">AI</div>
    </div>

    <div class="nav-top">
      <button
        v-for="item in topItems"
        :key="item.key"
        class="nav-btn"
        :class="{ active: active === item.key }"
        :title="item.label"
        @click="$emit('select', item.key)"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </div>

    <div class="nav-bottom">
      <button
        v-for="item in bottomItems"
        :key="item.key"
        class="nav-btn"
        :class="{ active: active === item.key }"
        :title="item.label"
        @click="$emit('select', item.key)"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
export type AppSection = 'chat' | 'observability'

defineProps<{
  active: AppSection
}>()

defineEmits<{
  select: [section: AppSection]
}>()

const topItems = [
  {
    key: 'chat' as AppSection,
    label: '对话',
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
  },
]

const bottomItems = [
  {
    key: 'observability' as AppSection,
    label: '监控',
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>`,
  },
]
</script>

<style scoped>
.narrow-nav {
  width: 72px;
  flex-shrink: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
  z-index: 10;
}

.nav-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 0;
  border-bottom: 1px solid #f3f4f6;
}

.logo-box {
  width: 32px;
  height: 32px;
  border-radius: 12px;
  background: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.3);
}

.nav-top {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 4px;
}

.nav-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 4px;
  border-top: 1px solid #f3f4f6;
}

.nav-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 56px;
  padding: 12px 0;
  border-radius: 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #9ca3af;
}

.nav-btn:hover {
  background: #f9fafb;
  color: #6b7280;
}

.nav-btn.active {
  background: #eef2ff;
  color: #4f46e5;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-btn.active .nav-icon {
  filter: none;
}

.nav-label {
  font-size: 10px;
  line-height: 1;
  white-space: nowrap;
  font-weight: 400;
}

.nav-btn.active .nav-label {
  font-weight: 600;
}
</style>
