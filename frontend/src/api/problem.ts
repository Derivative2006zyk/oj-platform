import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
})

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

export async function getProblems(params: {
  page?: number
  page_size?: number
  category_id?: number
  difficulty?: number
  type?: string
  tag?: string
  keyword?: string
}): Promise<ProblemListResponse> {
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
  const res = await api.post('/admin/problems', data, {
    headers: { 'X-Admin-Key': adminKey }
  })
  return res.data
}

export async function updateProblem(id: number, data: any): Promise<{ id: number }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  const res = await api.put(`/admin/problems/${id}`, data, {
    headers: { 'X-Admin-Key': adminKey }
  })
  return res.data
}

export async function deleteProblem(id: number): Promise<{ message: string }> {
  const adminKey = localStorage.getItem('admin_key') || ''
  const res = await api.delete(`/admin/problems/${id}`, {
    headers: { 'X-Admin-Key': adminKey }
  })
  return res.data
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