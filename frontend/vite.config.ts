import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  // 【核心修复】强制使用相对路径，这是 Capacitor / Cordova 打包解决白屏的必须配置！
  // 如果不加这行，打包后的 index.html 会去加载 /assets/xxx.js，在手机 file:// 协议下会直接 404 导致白屏。
  base: './',
  
  plugins: [vue()],
  
  server: {
    // 【新增】允许局域网内其他设备（如手机）通过 IP 访问 Vite 开发服务器
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        // 改用 127.0.0.1，比 localhost 更稳定，防止某些系统 IPv6 解析干扰
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
      // 代理插件静态文件请求
      '/plugins_static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  
  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      },
      '/plugins_static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
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