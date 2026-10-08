import './styles/tokens.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { refreshTrayFromBackend } from './utils/tauri'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

// 启动时若已登录，刷新托盘 tooltip
const token = localStorage.getItem('oj_token')
if (token) {
  // 延迟 2 秒，等 Tauri 端窗口加载完成
  setTimeout(() => {
    refreshTrayFromBackend(token).catch(() => {})
  }, 2000)
}