import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/axios'

export interface PluginManifest {
  name: string
  display_name: string
  version: string
  author: string
  description: string
  folder_name: string
  enabled?: boolean
  ui_manifest?: {
    menu_name: string
    route_path: string
    icon?: string
    order?: number
  }
}

export const usePluginStore = defineStore('plugin', () => {
  const plugins = ref<PluginManifest[]>([])

  async function fetchPlugins() {
    try {
      const res = await api.get<PluginManifest[]>('/plugins/ui?_t=' + Date.now())
      plugins.value = res.data
    } catch (e) {
      // 离线时静默失败，不污染控制台
      console.warn('[PluginStore] 插件列表获取失败，可能处于离线模式')
    }
  }

  return {
    plugins,
    fetchPlugins,
  }
})