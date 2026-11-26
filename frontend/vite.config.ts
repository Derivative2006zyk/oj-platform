import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 【新增】代理目标可配置，便于 E2E 指向独立测试栈
const API_TARGET = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

const proxyConfig = {
  '/api': {
    target: API_TARGET,
    changeOrigin: true,
    ws: true,
  },
  '/plugins_static': {
    target: API_TARGET,
    changeOrigin: true,
  },
}

export default defineConfig({
  // 强制使用相对路径，这是 Capacitor / Cordova 打包解决白屏的必须配置
  base: './',

  plugins: [vue()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: proxyConfig,
  },

  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: proxyConfig,
  },

  optimizeDeps: {
    include: ['monaco-editor'],
  },

  build: {
    rollupOptions: {
      output: {
        manualChunks(id: string) {
          if (id.includes('monaco-editor')) {
            return 'monaco'
          }
        },
      },
    },
  },
})