import api from '../utils/axios'
import { enqueueAction } from '../utils/offline-queue'

// 分类
export interface Category {
  id: number
  name: string
  description?: string
  sort_order: number
}

export async function getCategories(): Promise<Category[]> {
  const res = await api.get('/categories')
  return res.data
}

// 题目
export interface ProblemSummary {
  id: number
  title: string
  type: string
  difficulty: number
  tags: string[]
  category_id: number
}

export interface ProblemListResponse {
  total: number
  page: number
  page_size: number
  items: ProblemSummary[]
}

export async function getProblems(params: any): Promise<ProblemListResponse> {
  const res = await api.get('/problems', { params })
  return res.data
}

export async function getAllTags(): Promise<string[]> {
  const res = await api.get('/tags')
  return res.data
}

// 题目详情
export interface TestCase {
  input_data: string
  expected_output: string
}

export interface Subproject {
  id: number
  title: string
  description: string
  hint?: string
  reference_links: { title: string; url: string; note?: string }[]
  answer_guide?: string
  sort_order: number
}

export interface ProblemDetail {
  id: number
  title: string
  description: string
  type: string
  difficulty: number
  tags: string[]
  category_id: number
  explanation?: string
  options?: { key: string; content: string; is_correct: boolean }[]
  blanks?: { blank_index: number; correct_answers: string[]; match_rule: string }[]
  test_cases: TestCase[]
  subprojects: Subproject[]
}

export async function getProblemDetail(id: number): Promise<ProblemDetail> {
  const res = await api.get(`/problems/${id}`)
  return res.data
}

export async function getProblemAnswer(id: number): Promise<{ answer: string; explanation: string }> {
  const res = await api.get(`/problems/${id}/answer`)
  return res.data
}

// 管理
export async function createProblem(data: any): Promise<{ id: number }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  try {
    const res = await api.post('/admin/problems', data, {
      headers: { 'X-Admin-Key': adminKey }
    })
    return res.data
  } catch (e: any) {
    const isNetworkError = !e.response || e.code === 'ERR_NETWORK' || e.code === 'ECONNABORTED' || e.message?.includes('timeout') || e.response?.status === 502
    if (isNetworkError) {
      throw new Error('当前无网络，无法新建题目。请联网后重试。')
    }
    throw e
  }
}

export async function updateProblem(id: number, data: any): Promise<{ id: number }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  
  try {
    const res = await api.put(`/admin/problems/${id}`, data, {
      headers: { 'X-Admin-Key': adminKey }
    })
    return res.data
  } catch (e: any) {
    console.log('捕获到错误，准备判断是否离线：', e)
    
    // 如果是 409 冲突，直接抛出，让前端去提示刷新
    if (e.response?.status === 409) {
      throw e
    }
    
    // 【暴力兜底】除了 409 版本冲突，任何报错（502、超时、断网）全给它扔进离线队列！
    console.log('触发离线队列保存！')
    enqueueAction({
      id: Date.now().toString() + Math.random().toString(36).slice(2),
      method: 'put',
      url: `/admin/problems/${id}`,
      data: data,
      headers: { 'X-Admin-Key': adminKey },
      description: `修改题目 #${id}`
    })
    
    return { id, message: 'offline-saved' } as any
  }
}

export async function deleteProblem(id: number): Promise<{ message: string }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  try {
    const res = await api.delete(`/admin/problems/${id}`, {
      headers: { 'X-Admin-Key': adminKey }
    })
    return res.data
  } catch (e: any) {
    const isNetworkError = !e.response || e.code === 'ERR_NETWORK' || e.code === 'ECONNABORTED' || e.message?.includes('timeout') || e.response?.status === 502
    if (isNetworkError) {
      throw new Error('当前无网络，无法删除题目。请联网后重试。')
    }
    throw e
  }
}

// 图片
export async function uploadImage(file: File, problemId?: number): Promise<{ id: number; url: string }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  const formData = new FormData()
  formData.append('file', file)
  if (problemId) {
    formData.append('problem_id', String(problemId))
  }
  const res = await api.post('/admin/images', formData, {
    headers: {
      'X-Admin-Key': adminKey,
      'Content-Type': 'multipart/form-data'
    }
  })
  return res.data
}