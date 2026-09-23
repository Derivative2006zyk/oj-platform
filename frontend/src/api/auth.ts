import api from '../utils/axios'

export interface UserInfo {
  id: number
  username: string
  email: string
  role: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface LoginPayload {
  username: string
  password: string
}

export async function register(payload: RegisterPayload): Promise<UserInfo> {
  const res = await api.post<UserInfo>('/auth/register', payload)
  return res.data
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>('/auth/login', payload)
  return res.data
}

export async function getMe(): Promise<UserInfo> {
  const res = await api.get<UserInfo>('/users/me')
  return res.data
}