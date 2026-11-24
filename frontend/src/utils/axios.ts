import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { getApiBaseUrl } from './backend-url'
import {
  enqueueAction,
  shouldQueue,
  describeAction,
  type OfflineAction,
} from './offline-queue'

export const QUEUED_FLAG = '__queued__'

const api: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 5000,
})

api.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl()

  const token = localStorage.getItem('oj_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function isNetworkError(error: AxiosError): boolean {
  if (error.response) return false
  const code = (error as any).code
  return (
    code === 'ERR_NETWORK' ||
    code === 'ECONNABORTED' ||
    code === 'ERR_CANCELED' ||
    error.message?.includes('Network Error') ||
    error.message?.includes('timeout')
  )
}

function makeQueuedResponse(config: any) {
  return {
    data: { [QUEUED_FLAG]: true, queued: true },
    status: 202,
    statusText: 'Queued',
    headers: {},
    config,
  } as any
}

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    const config: any = error.config

    if (error.response?.status === 401) {
      localStorage.removeItem('oj_token')
      localStorage.removeItem('oj_user')
      if (!window.location.hash.includes('/login')) {
        window.location.href = '/#/login'
      }
      return Promise.reject(error)
    }

    const method = (config?.method || 'get').toUpperCase()
    const url = config?.url || ''

    // 断网 + 可重放写操作 → 入队，返回 202 伪响应
    if (config && isNetworkError(error) && shouldQueue(method, url)) {
      const headers: Record<string, string> = {}
      const adminKey = localStorage.getItem('admin_key')
      if (adminKey) headers['X-Admin-Key'] = adminKey

      let data = config.data
      if (typeof data === 'string') {
        try { data = JSON.parse(data) } catch {}
      }

      const action: OfflineAction = enqueueAction({
        method: method.toLowerCase() as OfflineAction['method'],
        url,
        data,
        headers,
        description: describeAction(method, url, data),
      })

      console.log(`[OfflineQueue] 断网，已暂存: ${action.description}`)
      return Promise.resolve(makeQueuedResponse(config))
    }

    return Promise.reject(error)
  }
)

export default api