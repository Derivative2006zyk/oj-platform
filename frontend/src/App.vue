<template>
  <div id="app-root">
    <NavBar />
    <div v-if="showBar" class="global-offline-bar">
      <span class="bar-dot" :class="offline ? 'bad' : 'ok'"></span>
      <span class="bar-text">
        {{ offline ? '当前离线' : '网络已恢复' }}
        <template v-if="pendingCount > 0"> · {{ pendingCount }} 项待同步</template>
        <template v-else-if="conflictCount > 0"> · {{ conflictCount }} 项同步冲突</template>
        <template v-else-if="deadCount > 0"> · {{ deadCount }} 项同步失败</template>
      </span>
      <router-link v-if="hasItems" to="/settings" class="bar-link">查看</router-link>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import NavBar from './components/NavBar.vue'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { App as CapacitorApp } from '@capacitor/app'
import {
  initOfflineQueue,
  processQueue,
  getQueue,
  getPendingCount,
  getDeadCount,
} from './utils/offline-queue'

let syncHandler: () => void
let queueHandler: () => void
let onlineHandler: () => void
let offlineHandler: () => void
let removeBackListener: (() => void) | null = null

const offline = ref(navigator.onLine === false)
const pendingCount = ref(0)
const deadCount = ref(0)
const conflictCount = ref(0)

const hasItems = computed(() => getQueue().length > 0)
const showBar = computed(
  () => offline.value || pendingCount.value > 0 || conflictCount.value > 0 || deadCount.value > 0
)

function refreshCounts() {
  pendingCount.value = getPendingCount()
  deadCount.value = getDeadCount()
  conflictCount.value = getQueue().filter(a => a.status === 'conflict').length
}

function bindKeyboardInset() {
  const vv = window.visualViewport
  if (!vv) return

  const apply = () => {
    const inset = Math.max(0, window.innerHeight - vv.height - vv.offsetTop)
    document.documentElement.style.setProperty('--keyboard-inset', inset + 'px')
  }

  vv.addEventListener('resize', apply)
  vv.addEventListener('scroll', apply)
  apply()
}

function bindBackButton() {
  CapacitorApp.addListener('backButton', ({ canGoBack }) => {
    const closable = document.querySelector('.drawer-mask:not([hidden]), .modal-mask')
    if (closable) return

    if (canGoBack) window.history.back()
    else CapacitorApp.exitApp()
  }).then(handle => {
    removeBackListener = () => handle.remove()
  }).catch(() => {})
}

onMounted(() => {
  initOfflineQueue()
  refreshCounts()

  if (navigator.onLine) processQueue()

  syncHandler = () => {
    refreshCounts()
    console.log('检测到队列同步完成，当前页面数据将更新')
  }
  queueHandler = () => refreshCounts()

  onlineHandler = () => {
    offline.value = false
    processQueue()
  }
  offlineHandler = () => { offline.value = true }

  window.addEventListener('offline-queue-synced', syncHandler)
  window.addEventListener('offline-queue-changed', queueHandler)
  window.addEventListener('online', onlineHandler)
  window.addEventListener('offline', offlineHandler)

  bindKeyboardInset()
  bindBackButton()
})

onUnmounted(() => {
  window.removeEventListener('offline-queue-synced', syncHandler)
  window.removeEventListener('offline-queue-changed', queueHandler)
  window.removeEventListener('online', onlineHandler)
  window.removeEventListener('offline', offlineHandler)
  removeBackListener?.()
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

.global-offline-bar {
  position: sticky;
  top: 56px;
  z-index: 9;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border-bottom: 1px solid var(--color-border-light);
}

.bar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bar-dot.bad { background: #ef4444; }
.bar-dot.ok { background: #10b981; }

.bar-text { flex: 1; min-width: 0; }

.bar-link {
  color: var(--color-primary);
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .global-offline-bar { top: 56px; padding: 6px 12px; font-size: 12px; }
}
</style>