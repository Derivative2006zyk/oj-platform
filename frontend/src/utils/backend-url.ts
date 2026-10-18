const URL_KEY = 'oj_backend_url'

// 判断是否在 Tauri 桌面端环境
export function isTauriEnv(): boolean {
  return typeof window !== 'undefined' && !!(window as any).__TAURI_INTERNALS__
}

// 获取当前配置的后端地址
export function getBackendUrl(): string {
  const saved = localStorage.getItem(URL_KEY)
  if (saved) {
    return saved.replace(/\/$/, '') // 移除末尾的斜杠
  }
  
  // 默认值：如果在桌面端，默认连接本机；如果是浏览器或移动端，默认空（走当前域名的相对路径）
  if (isTauriEnv()) {
    return 'http://127.0.0.1:8000'
  }
  return ''
}

// 保存后端地址
export function setBackendUrl(url: string): void {
  if (!url) {
    localStorage.removeItem(URL_KEY)
  } else {
    localStorage.setItem(URL_KEY, url.trim().replace(/\/$/, ''))
  }
}

// 获取用于 Axios 的 baseURL
export function getApiBaseUrl(): string {
  const base = getBackendUrl()
  return base ? `${base}/api` : '/api'
}

// 获取用于 WebSocket 的 baseURL
export function getWsBaseUrl(): string {
  const base = getBackendUrl()
  if (!base) {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}`
  }
  return base.replace(/^http/, 'ws')
}