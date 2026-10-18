import { getWsBaseUrl } from './backend-url'

export interface WSMessage {
  type: 'status' | 'judged'
  submission_id: number
  status: string
  passed_cases?: number
  total_cases?: number
  runtime_ms?: number
}

export interface SubmissionWSHandle {
  close: () => void
  isOpen: () => boolean
}

export function openSubmissionWS(
  submissionId: number,
  onMessage: (msg: WSMessage) => void,
  onError?: (e: Event) => void
): SubmissionWSHandle {
  const token = localStorage.getItem('oj_token') || ''
  
  // 动态获取 WebSocket Base URL
  const base = getWsBaseUrl()
  const url = `${base}/api/submissions/${submissionId}/ws?token=${encodeURIComponent(token)}`
  
  const ws = new WebSocket(url)

  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data) as WSMessage)
    } catch (err) {
      console.warn('WS message parse error', err)
    }
  }

  ws.onerror = (e) => {
    if (onError) onError(e)
  }

  return {
    close: () => {
      try { ws.close() } catch {}
    },
    isOpen: () => ws.readyState === WebSocket.OPEN,
  }
}