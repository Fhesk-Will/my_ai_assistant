<template>
  <div id="app-container">
    <NarrowNav :active="activeSection" @select="navigate" />
    <div class="content-area">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import NarrowNav, { type AppSection } from './components/NarrowNav.vue'

const router = useRouter()
const route = useRoute()

const activeSection = computed<AppSection>(() => {
  if (route.name === 'observability') return 'observability'
  return 'chat'
})

function navigate(section: AppSection) {
  if (section === 'observability') {
    router.push('/observability')
  } else {
    router.push('/')
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #ffffff;
  color: #374151;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app-container {
  height: 100vh;
  display: flex;
  overflow: hidden;
}

.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
