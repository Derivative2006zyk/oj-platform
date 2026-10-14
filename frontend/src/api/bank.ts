import api from '../utils/axios'

export interface ExportOptions {
  problem_ids?: number[] | null
}

export async function exportBank(options: ExportOptions = {}): Promise<void> {
  const adminKey = localStorage.getItem('admin_key') || ''

  const res = await api.post('/admin/bank/export', options, {
    headers: { 'X-Admin-Key': adminKey },
    responseType: 'blob',
  })

  const disposition = res.headers['content-disposition'] || ''
  let filename = `ojbank_${Date.now()}.zip`
  const m = /filename="?([^";]+)"?/.exec(disposition)
  if (m) filename = m[1]

  const blob = new Blob([res.data], { type: 'application/zip' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export interface Bank {
  id: number
  name: string
  description: string | null
  sort_order: number
  created_at: string
  problem_count: number
}

export async function listBanks(): Promise<Bank[]> {
  const res = await api.get<Bank[]>('/banks')
  return res.data
}

export async function createBank(data: {
  name: string
  description?: string
  sort_order?: number
}): Promise<Bank> {
  const adminKey = localStorage.getItem('admin_key') || ''
  const res = await api.post<Bank>('/admin/banks', data, {
    headers: { 'X-Admin-Key': adminKey },
  })
  return res.data
}

export async function updateBank(id: number, data: Partial<Bank>): Promise<Bank> {
  const adminKey = localStorage.getItem('admin_key') || ''
  const res = await api.put<Bank>(`/admin/banks/${id}`, data, {
    headers: { 'X-Admin-Key': adminKey },
  })
  return res.data
}

export async function deleteBank(id: number): Promise<void> {
  const adminKey = localStorage.getItem('admin_key') || ''
  await api.delete(`/admin/banks/${id}`, {
    headers: { 'X-Admin-Key': adminKey },
  })
}