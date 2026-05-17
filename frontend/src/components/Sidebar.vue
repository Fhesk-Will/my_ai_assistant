<template>
  <aside class="sidebar">
    <div class="sidebar-new-chat">
      <button class="btn-new-chat" @click="$emit('newChat')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新建对话
      </button>
    </div>

    <div class="session-list">
      <div v-for="group in groupedSessions" :key="group.label" class="session-group">
        <div class="group-label">{{ group.label }}</div>
        <div class="group-items">
          <div
            v-for="session in group.items"
            :key="session.id"
            class="session-item"
            :class="{ active: session.id === activeId }"
            @click="$emit('select', session.id)"
            @mouseenter="hoveredId = session.id"
            @mouseleave="hoveredId = null"
          >
            <template v-if="renamingId === session.id">
              <input
                ref="renameInput"
                v-model="renameValue"
                class="rename-input"
                @keydown.enter="confirmRename(session.id)"
                @keydown.escape="cancelRename"
                @blur="confirmRename(session.id)"
                @click.stop
              />
            </template>
            <template v-else>
              <span class="session-title">{{ session.title }}</span>
              <button
                class="btn-dots"
                :class="{ visible: hoveredId === session.id || activeId === session.id }"
                @click.stop="openMenu(session.id, $event)"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/></svg>
              </button>
            </template>
          </div>
        </div>
      </div>
      <div v-if="sessions.length === 0" class="empty-hint">暂无对话</div>
    </div>

    <!-- Context Menu -->
    <Teleport to="body">
      <div v-if="menuState" class="context-overlay" @click="closeMenu" />
      <div
        v-if="menuState"
        class="context-menu"
        :style="{ top: menuState.y + 'px', left: menuState.x + 'px' }"
      >
        <button class="context-item" @click="startRename">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>
          重命名
        </button>
        <div class="context-divider" />
        <button class="context-item danger" @click="handleDelete">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          删除
        </button>
      </div>
    </Teleport>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, nextTick } from 'vue'
import type { Session } from '../api/client'

const props = defineProps<{
  sessions: Session[]
  activeId: string
}>()

const emit = defineEmits<{
  select: [id: string]
  rename: [id: string, title: string]
  delete: [id: string]
  newChat: []
}>()

const hoveredId = ref<string | null>(null)
const menuState = ref<{ id: string; x: number; y: number } | null>(null)
const renamingId = ref<string | null>(null)
const renameValue = ref('')
const renameInput = ref<HTMLInputElement | null>(null)

const groupedSessions = computed(() => {
  const today: Session[] = []
  const yesterday: Session[] = []
  const earlier: Session[] = []

  for (const s of props.sessions) {
    const t = s.time
    if (t.includes('今天') || t.includes(new Date().toLocaleDateString('zh-CN'))) {
      today.push(s)
    } else if (t.includes('昨天')) {
      yesterday.push(s)
    } else {
      earlier.push(s)
    }
  }

  // Fallback grouping by position if time parsing doesn't work
  if (today.length === 0 && yesterday.length === 0 && earlier.length === props.sessions.length) {
    const groups: { label: string; items: Session[] }[] = []
    if (props.sessions.length > 0) {
      groups.push({ label: '今天', items: props.sessions.slice(0, Math.min(3, props.sessions.length)) })
    }
    if (props.sessions.length > 3) {
      groups.push({ label: '昨天', items: props.sessions.slice(3, Math.min(5, props.sessions.length)) })
    }
    if (props.sessions.length > 5) {
      groups.push({ label: '更早', items: props.sessions.slice(5) })
    }
    return groups
  }

  const groups: { label: string; items: Session[] }[] = []
  if (today.length) groups.push({ label: '今天', items: today })
  if (yesterday.length) groups.push({ label: '昨天', items: yesterday })
  if (earlier.length) groups.push({ label: '更早', items: earlier })
  return groups
})

function openMenu(id: string, event: MouseEvent) {
  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  menuState.value = { id, x: rect.right + 4, y: rect.top }
}

function closeMenu() {
  menuState.value = null
}

function startRename() {
  if (!menuState.value) return
  const session = props.sessions.find(s => s.id === menuState.value!.id)
  renameValue.value = session?.title || ''
  renamingId.value = menuState.value.id
  menuState.value = null
  nextTick(() => {
    const el = document.querySelector('.rename-input') as HTMLInputElement
    el?.focus()
    el?.select()
  })
}

function confirmRename(id: string) {
  if (renameValue.value.trim()) {
    emit('rename', id, renameValue.value.trim())
  }
  renamingId.value = null
  renameValue.value = ''
}

function cancelRename() {
  renamingId.value = null
  renameValue.value = ''
}

function handleDelete() {
  if (!menuState.value) return
  emit('delete', menuState.value.id)
  menuState.value = null
}
</script>

<style scoped>
.sidebar {
  width: 264px;
  flex-shrink: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f7f7f8;
  border-right: 1px solid #e5e7eb;
}

.sidebar-new-chat {
  padding: 16px 16px 12px;
}

.btn-new-chat {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  background: #4f46e5;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.15s ease;
}

.btn-new-chat:hover {
  background: #4338ca;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px 12px;
}

.session-group {
  margin-bottom: 16px;
}

.group-label {
  padding: 0 8px 4px;
  font-size: 12px;
  color: #9ca3af;
  letter-spacing: 0.5px;
}

.group-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.session-item:hover {
  background: rgba(229, 231, 235, 0.6);
}

.session-item.active {
  background: #eef2ff;
  color: #4338ca;
}

.session-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-dots {
  flex-shrink: 0;
  padding: 4px;
  border-radius: 8px;
  border: none;
  background: transparent;
  cursor: pointer;
  opacity: 0;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-dots.visible {
  opacity: 1;
}

.session-item.active .btn-dots {
  color: #6366f1;
}

.session-item.active .btn-dots:hover {
  color: #4338ca;
  background: #c7d2fe;
}

.btn-dots:hover {
  color: #6b7280;
  background: #e5e7eb;
}

.rename-input {
  width: 100%;
  background: white;
  border: 1px solid #6366f1;
  border-radius: 8px;
  padding: 2px 8px;
  font-size: 13px;
  color: #1f2937;
  outline: none;
}

.rename-input:focus {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}

.empty-hint {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 20px;
}

.context-overlay {
  position: fixed;
  inset: 0;
  z-index: 48;
}

.context-menu {
  position: fixed;
  z-index: 50;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  border: 1px solid #f3f4f6;
  padding: 6px;
  min-width: 140px;
  overflow: hidden;
}

.context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #374151;
  border-radius: 8px;
  transition: background 0.1s ease;
}

.context-item:hover {
  background: #f9fafb;
}

.context-item.danger {
  color: #ef4444;
}

.context-item.danger:hover {
  background: #fef2f2;
}

.context-divider {
  margin: 4px 10px;
  border-top: 1px solid #f3f4f6;
}
</style>
