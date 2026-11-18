<template>
  <div id="app-root">
    <NavBar />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import NavBar from './components/NavBar.vue'
import { onMounted, onUnmounted } from 'vue'
import { initOfflineQueue, processQueue } from './utils/offline-queue'

let syncHandler: () => void

onMounted(() => {
  initOfflineQueue()
  if (navigator.onLine) {
    processQueue()
  }
  syncHandler = () => {
    console.log('检测到队列同步完成，当前页面数据将更新')
  }
  window.addEventListener('offline-queue-synced', syncHandler)
})

onUnmounted(() => {
  window.removeEventListener('offline-queue-synced', syncHandler)
})
</script>

<style>
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  min-height: 100%;
  width: 100%;
  /* 移除 overflow-x: auto，避免 body 成为滚动容器导致 sticky 失效 */
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  background-color: var(--color-bg-page);
  -webkit-touch-callout: none;
}

#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
  /* 移除 min-width: 100vw 和 overflow-x: auto，横向溢出交给具体元素自己控制 */
}

a {
  color: inherit;
  text-decoration: none;
}

pre {
  overflow-x: auto;
  max-width: 100%;
}

img {
  max-width: 100%;
  height: auto;
}
</style>