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

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${proto}//${location.host}/api/submissions/${submissionId}/ws?token=${encodeURIComponent(token)}`

  const ws = new WebSocket(url)

  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as WSMessage
      onMessage(data)
    } catch (err) {
      console.warn('WS message parse error', err)
    }
  }

  ws.onerror = (e) => {
    if (onError) onError(e)
  }

  return {
    close: () => {
      try {
        ws.close()
      } catch {}
    },
    isOpen: () => ws.readyState === WebSocket.OPEN,
  }
}