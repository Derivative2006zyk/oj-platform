import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import * as authApi from '../api/auth'
import type { UserInfo, RegisterPayload, LoginPayload } from '../api/auth'

const TOKEN_KEY = 'oj_token'
const USER_KEY = 'oj_user'

function readUserFromStorage(): UserInfo | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as UserInfo
  } catch {
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<UserInfo | null>(readUserFromStorage())

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setSession(newToken: string, newUser: UserInfo) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem(TOKEN_KEY, newToken)
    localStorage.setItem(USER_KEY, JSON.stringify(newUser))
  }

  function clearSession() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  async function register(payload: RegisterPayload): Promise<UserInfo> {
    return await authApi.register(payload)
  }

  async function fetchMe(): Promise<UserInfo> {
    const u = await authApi.getMe()
    user.value = u
    localStorage.setItem(USER_KEY, JSON.stringify(u))
    return u
  }

  async function login(payload: LoginPayload): Promise<UserInfo> {
    const res = await authApi.login(payload)

    // 先存 token，让拦截器能带上
    token.value = res.access_token
    localStorage.setItem(TOKEN_KEY, res.access_token)

    // 拉用户信息
    const u = await fetchMe()

    return u
  }

  function logout() {
    clearSession()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    setSession,
    clearSession,
    register,
    login,
    fetchMe,
    logout,
  }
})