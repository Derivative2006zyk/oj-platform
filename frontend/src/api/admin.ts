import api from '../utils/axios'

export interface AdminUser {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface AdminUserListResponse {
  total: number
  page: number
  page_size: number
  items: AdminUser[]
}

export interface AdminStats {
  total_users: number
  total_admins: number
  active_users: number
  banned_users: number
  total_submissions: number
  total_accepted: number
  total_problems: number
}

export async function listUsers(params: {
  page?: number
  page_size?: number
  role?: string
  is_active?: boolean
  keyword?: string
} = {}): Promise<AdminUserListResponse> {
  const res = await api.get<AdminUserListResponse>('/admin/users', { params })
  return res.data
}

export async function changeUserRole(
  userId: number,
  role: string,
): Promise<AdminUser> {
  const res = await api.put<AdminUser>(`/admin/users/${userId}/role`, { role })
  return res.data
}

export async function changeUserStatus(
  userId: number,
  isActive: boolean,
): Promise<AdminUser> {
  const res = await api.put<AdminUser>(`/admin/users/${userId}/status`, {
    is_active: isActive,
  })
  return res.data
}

export async function getAdminStats(): Promise<AdminStats> {
  const res = await api.get<AdminStats>('/admin/stats')
  return res.data
}