<template>
  <main class="plugin-page">
    <div class="container">
      <div class="plugin-header">
        <h1>插件: {{ pluginInfo?.display_name || pluginName }}</h1>
        <span class="version">v{{ pluginInfo?.version }}</span>
        <a :href="iframeUrl" target="_blank" class="open-new">在新窗口打开</a>
      </div>
      
      <div class="iframe-container">
        <iframe 
          v-if="iframeUrl" 
          :src="iframeUrl" 
          frameborder="0"
          class="plugin-iframe"
        ></iframe>
        <div v-else class="empty">
          该插件未提供前端页面
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePluginStore } from '../stores/plugin'
import { getBackendUrl } from '../utils/backend-url'

const route = useRoute()
const pluginStore = usePluginStore()

const pluginName = computed(() => route.params.name as string)
const pluginInfo = computed(() => 
  pluginStore.plugins.find(p => p.folder_name === pluginName.value)
)

const iframeUrl = computed(() => {
  const base = getBackendUrl()
  // 如果 base 存在，使用绝对路径；如果为空，在开发环境下使用相对路径
  const prefix = base || ''
  return `${prefix}/plugins_static/${pluginName.value}/frontend/index.html`
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
</style>