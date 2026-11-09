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
  // 如果启动时正好有网，尝试同步一次（防止上次断网没发出去的）
  if (navigator.onLine) {
    processQueue()
  }
  
  // 监听同步完成事件，如果在某些特定页面可能需要刷新数据
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
  /* 允许双指放大后出现横向滚动条 */
  overflow-x: auto;
}

body {
  font-family: var(--font-family-base);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  background-color: var(--color-bg-page);
  /* 防止放大时触摸变成选中文本（可选，防止误触） */
  -webkit-touch-callout: none;
}

#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: 100%;
  overflow-x: auto;
  /* 确保内容区撑满 */
  min-width: 100vw; 
}

a {
  color: inherit;
  text-decoration: none;
}
</style>