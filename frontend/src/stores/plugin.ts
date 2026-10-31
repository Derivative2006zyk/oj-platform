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
  enabled?: boolean // 新增：启用状态
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
      console.error('获取插件列表失败', e)
    }
  }

  return {
    plugins,
    fetchPlugins,
  }
})