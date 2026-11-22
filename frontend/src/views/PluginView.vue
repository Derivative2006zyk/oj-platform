<template>
  <main class="plugin-page">
    <div class="container">
      <div class="plugin-header">
        <h1>插件: {{ pluginInfo?.display_name || pluginName }}</h1>
        <span class="version">v{{ pluginInfo?.version }}</span>
        <a :href="newWindowUrl" target="_blank" rel="noopener" class="open-new">在新窗口打开</a>
      </div>

      <div class="iframe-container">
        <!-- 加载遮罩 -->
        <div v-if="loading" class="loading-mask">
          <div class="spinner"></div>
          <div>正在加载插件页面...</div>
        </div>

        <iframe
          v-if="iframeUrl"
          ref="iframeRef"
          :key="pluginName"
          :src="iframeUrl"
          frameborder="0"
          sandbox="allow-scripts allow-same-origin allow-modals allow-forms"
          class="plugin-iframe"
          @load="onIframeLoad"
        ></iframe>

        <div v-else class="empty">
          该插件未提供前端页面
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePluginStore } from '../stores/plugin'
import { getBackendUrl } from '../utils/backend-url'

const route = useRoute()
const router = useRouter()
const pluginStore = usePluginStore()

const loading = ref(true)
const iframeRef = ref<HTMLIFrameElement | null>(null)

// 【缓存修复】每次进入插件页使用一次性的时间戳，避免 iframe 命中旧磁盘缓存
const cacheBuster = ref(Date.now())

const pluginName = computed(() => route.params.name as string)
const pluginInfo = computed(() =>
  pluginStore.plugins.find(p => p.folder_name === pluginName.value)
)

const iframeUrl = computed(() => {
  if (!pluginName.value) return ''
  const base = getBackendUrl()
  const name = encodeURIComponent(pluginName.value)
  return `${base || ''}/plugins_static/${name}/frontend/index.html?v=${cacheBuster.value}`
})

/**
 * 新窗口打开时无法使用 postMessage，改为把上下文放进 URL。
 * 注意：Token 会出现在该窗口地址栏中，仅建议在本地/可信环境使用。
 */
const newWindowUrl = computed(() => {
  const url = new URL(iframeUrl.value || '/', window.location.href)
  const token = localStorage.getItem('oj_token')
  const adminKey = localStorage.getItem('admin_key')
  const base = getBackendUrl()
  const theme = document.documentElement.getAttribute('data-theme') || 'light'

  if (token) url.searchParams.set('token', token)
  if (adminKey) url.searchParams.set('admin_key', adminKey)
  if (base) url.searchParams.set('api', base)
  url.searchParams.set('theme', theme)

  return url.toString()
})

function postContext() {
  const win = iframeRef.value?.contentWindow
  if (!win) return

  win.postMessage({
    type: 'oj:context',
    apiBase: getBackendUrl(),
    token: localStorage.getItem('oj_token') || '',
    adminKey: localStorage.getItem('admin_key') || '',
    theme: document.documentElement.getAttribute('data-theme') || 'light'
  }, '*')
}

function postTheme() {
  const win = iframeRef.value?.contentWindow
  if (!win) return

  win.postMessage({
    type: 'oj:theme',
    theme: document.documentElement.getAttribute('data-theme') || 'light'
  }, '*')
}

function onIframeLoad() {
  loading.value = false
  // 插件页面即使不发 ready，也主动推一次上下文
  postContext()
}

function onIframeMessage(event: MessageEvent) {
  if (!iframeRef.value || event.source !== iframeRef.value.contentWindow) return

  const data = event.data
  if (!data || typeof data !== 'object') return

  if (data.type === 'oj:plugin-ready') {
    postContext()
    return
  }

  if (
    data.type === 'oj:navigate' &&
    typeof data.path === 'string' &&
    data.path.startsWith('/') &&
    !data.path.startsWith('//')
  ) {
    router.push(data.path)
    return
  }

  if (data.type === 'oj:set-admin-key' && typeof data.adminKey === 'string') {
    localStorage.setItem('admin_key', data.adminKey)
  }
}

let themeObserver: MutationObserver | null = null

onMounted(() => {
  window.addEventListener('message', onIframeMessage)

  themeObserver = new MutationObserver(postTheme)
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  })
})

onUnmounted(() => {
  window.removeEventListener('message', onIframeMessage)
  themeObserver?.disconnect()
  themeObserver = null
})

// 路由参数变化时，重置加载状态并刷新缓存参数
watch(() => route.params.name, () => {
  loading.value = true
  cacheBuster.value = Date.now()
})
</script>

<style scoped>
.plugin-page {
  padding: var(--spacing-lg) 0;
  height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
}

.container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.plugin-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.plugin-header h1 {
  font-size: var(--font-size-title);
  margin: 0;
}

.version {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.open-new {
  margin-left: auto;
  color: var(--color-primary);
  text-decoration: underline;
}

.iframe-container {
  flex: 1;
  min-height: 0;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  display: flex;
  position: relative;
}

.plugin-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.empty {
  margin: auto;
  color: var(--color-text-muted);
}

/* 加载遮罩 */
.loading-mask {
  position: absolute;
  inset: 0;
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--color-text-secondary);
  z-index: 10;
}

.spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .plugin-page {
    padding: 0;
    height: calc(100dvh - 56px);
  }
  .container {
    padding: 0;
  }
  .plugin-header {
    padding: 10px 12px;
    margin-bottom: 0;
  }
  .plugin-header h1 {
    font-size: 16px;
  }
  .open-new {
    font-size: 12px;
  }
  .iframe-container {
    border-radius: 0;
    box-shadow: none;
  }
}
</style>