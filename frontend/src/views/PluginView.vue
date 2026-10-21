<template>
  <main class="plugin-page">
    <div class="container">
      <header class="page-header">
        <h1>插件页面: {{ pluginName }}</h1>
      </header>
      <section class="card">
        <div class="card-body">
          <p>此处用于渲染动态加载的插件前端内容。</p>
          <p v-if="pluginInfo">
            插件作者: {{ pluginInfo.author }} | 版本: {{ pluginInfo.version }}
          </p>
          <p v-else>未找到该插件的详细信息。</p>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePluginStore } from '../stores/plugin'

const route = useRoute()
const pluginStore = usePluginStore()

const pluginName = computed(() => route.params.name as string)
const pluginInfo = computed(() => 
  pluginStore.plugins.find(p => p.folder_name === pluginName.value)
)
</script>

<style scoped>
.plugin-page {
  padding: var(--spacing-xl) 0;
}
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}
.page-header {
  margin-bottom: var(--spacing-lg);
}
.page-header h1 {
  font-size: var(--font-size-title);
  margin: 0;
}
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}
.card-body {
  padding: var(--spacing-lg);
}
</style>