import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { getApiBaseUrl } from './backend-url'

const api: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  // 每次请求前重新获取 baseURL，确保修改设置后立即生效
  config.baseURL = getApiBaseUrl()
  
  const token = localStorage.getItem('oj_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('oj_token')
      localStorage.removeItem('oj_user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api