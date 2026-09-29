import api from '../utils/axios'

export interface UserStats {
  total_submissions: number
  accepted_submissions: number
  solved_problems: number
  acceptance_rate: number
  language_distribution: Record<string, number>
}

export async function getMyStats(): Promise<UserStats> {
  const res = await api.get<UserStats>('/users/me/stats')
  return res.data
}

export async function changePassword(
  oldPassword: string,
  newPassword: string,
): Promise<{ message: string }> {
  const res = await api.put('/users/me/password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
  return res.data
}