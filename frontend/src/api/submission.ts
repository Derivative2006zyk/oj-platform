import api from '../utils/axios'
import { enqueueAction } from '../utils/offline-queue'

export interface SubmissionDetail {
  id: number
  user_id: number
  problem_id: number
  submission_kind: string
  code: string | null
  language: string
  answer_data: Record<string, any> | null
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
  code?: string | null
  language: string
  answer_data?: Record<string, any> | null
}

export async function submitCode(data: SubmissionCreate): Promise<SubmissionDetail> {
  try {
    const res = await api.post<SubmissionDetail>('/submissions', data)
    return res.data
  } catch (e: any) {
    // 【拦截】如果是网络断开或 502
    const isNetworkError = !e.response || e.code === 'ERR_NETWORK' || e.code === 'ECONNABORTED' || e.message?.includes('timeout') || e.response?.status === 502
    
    if (isNetworkError) {
      console.log('[API] 离线提交触发，加入队列')
      
      enqueueAction({
        id: Date.now().toString() + Math.random().toString(36).slice(2),
        method: 'post',
        url: '/submissions',
        data: data,
        description: `提交答案 (题目 #${data.problem_id})`
      })

      // 【伪造返回】欺骗 UI 层，让它知道这是离线状态
      const offlineSub: SubmissionDetail = {
        id: -Math.floor(Math.random() * 10000), // 负数 ID
        user_id: 0, 
        problem_id: data.problem_id,
        submission_kind: data.language === 'choice' ? 'choice' : 'code', // 粗略推断
        code: data.code || null,
        language: data.language,
        answer_data: data.answer_data || null,
        status: 'OFFLINE_PENDING', // 核心状态标记
        runtime_ms: null,
        memory_kb: null,
        passed_cases: 0,
        total_cases: 0,
        error_message: '当前处于离线状态，答案已保存在本地，联网后将自动提交评测。',
        created_at: new Date().toISOString()
      }
      
      return offlineSub
    }
    
    throw e
  }
}

export async function getSubmission(id: number): Promise<SubmissionDetail> {
  const res = await api.get<SubmissionDetail>(`/submissions/${id}`)
  return res.data
}

export async function listMySubmissions(params: {
  page?: number
  page_size?: number
  status?: string
  problem_id?: number
} = {}): Promise<any> {
  const res = await api.get('/submissions', { params })
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