import api from '../utils/axios'
import { getBackendUrl } from '../utils/backend-url'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export async function getAIConfig(): Promise<any> {
  const res = await api.get('/plugins/ai/config')
  return res.data.config
}

export async function saveAIConfig(config: any): Promise<void> {
  await api.put('/plugins/ai/config', { config })
}

export async function streamChat(
  messages: ChatMessage[],
  onChunk: (text: string) => void,
  onError: (err: any) => void,
  onComplete: () => void
) {
  let base = getBackendUrl()
  if (base.endsWith('/')) base = base.slice(0, -1)
  const url = `${base}/api/plugins/ai/chat`
  const token = localStorage.getItem('oj_token') || ''

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` // 携带鉴权 Token
      },
      body: JSON.stringify({ messages })
    })

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    if (!reader) throw new Error('No reader available')

    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          let data = line.slice(6).replace(/\r$/, '')
          if (data.trim() === '[DONE]') {
            onComplete()
            return
          }
          data = data.replace(/\\n/g, '\n')
          onChunk(data)
        }
      }
    }
    onComplete()
  } catch (e) {
    onError(e)
  }
}