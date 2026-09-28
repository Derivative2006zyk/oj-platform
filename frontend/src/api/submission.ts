import api from '../utils/axios'

export interface SubmissionDetail {
  id: number
  user_id: number
  problem_id: number
  code: string
  language: string
  status: string
  runtime_ms: number | null
  memory_kb: number | null
  passed_cases: number
  total_cases: number
  error_message: string | null
  created_at: string
}

export interface SubmissionCreate {
  problem_id: number
  code: string
  language: string
}

export async function submitCode(data: SubmissionCreate): Promise<SubmissionDetail> {
  const res = await api.post<SubmissionDetail>('/submissions', data)
  return res.data
}

export async function getSubmission(id: number): Promise<SubmissionDetail> {
  const res = await api.get<SubmissionDetail>(`/submissions/${id}`)
  return res.data
}

export async function listMySubmissions(page: number = 1, pageSize: number = 20): Promise<any> {
  const res = await api.get('/submissions', {
    params: { page, page_size: pageSize },
  })
  return res.data
}

export async function listProblemSubmissions(
  problemId: number,
  page: number = 1,
  pageSize: number = 20,
): Promise<any> {
  const res = await api.get(`/problems/${problemId}/submissions`, {
    params: { page, page_size: pageSize },
  })
  return res.data
}