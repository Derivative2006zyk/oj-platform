import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { getApiBaseUrl } from './backend-url'

const api: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 5000, // 【修改】把超时从 3000 提到 5000，防止手机网络慢导致误判
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

api.interceptors.response.use(
  (res) => res,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('oj_token')
      localStorage.removeItem('oj_user')
      // 【修复】适配 Hash 路由，跳转到 /#/login
      if (!window.location.hash.includes('/login')) {
        window.location.href = '/#/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api