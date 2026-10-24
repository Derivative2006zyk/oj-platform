<template>
  <main class="plugin-page">
    <div class="container">
      <div class="plugin-header">
        <h1>插件: {{ pluginInfo?.display_name || pluginName }}</h1>
        <span class="version">v{{ pluginInfo?.version }}</span>
        <a :href="iframeUrl" target="_blank" class="open-new">在新窗口打开</a>
      </div>
      
      <div class="iframe-container">
        <!-- 加载遮罩 -->
        <div v-if="loading" class="loading-mask">
          <div class="spinner"></div>
          <div>正在加载插件页面...</div>
        </div>

        <iframe 
          v-if="iframeUrl" 
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
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePluginStore } from '../stores/plugin'
import { getBackendUrl } from '../utils/backend-url'

const route = useRoute()
const pluginStore = usePluginStore()

const loading = ref(true)

const pluginName = computed(() => route.params.name as string)
const pluginInfo = computed(() => 
  pluginStore.plugins.find(p => p.folder_name === pluginName.value)
)

const iframeUrl = computed(() => {
  const base = getBackendUrl()
  const prefix = base || ''
  return `${prefix}/plugins_static/${pluginName.value}/frontend/index.html`
})

function onIframeLoad() {
  loading.value = false
}

// 路由参数变化时，重置加载状态
watch(() => route.params.name, () => {
  loading.value = true
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
</style>