import api from './axios'
import { setCache, getCache } from './cache'

export interface OfflineAction {
  id: string // 唯一标识（时间戳+随机数）
  method: 'post' | 'put' | 'delete'
  url: string
  data?: any
  headers?: any
  description: string // 例如："修改题目 #12"
}

const QUEUE_KEY = 'oj_offline_queue'

export function getQueue(): OfflineAction[] {
  return getCache<OfflineAction[]>(QUEUE_KEY) || []
}

export function enqueueAction(action: OfflineAction) {
  const queue = getQueue()
  queue.push(action)
  setCache(QUEUE_KEY, queue)
  console.log(`[OfflineQueue] 已加入队列: ${action.description}`)
}

export function removeActionFromQueue(id: string) {
  let queue = getQueue()
  queue = queue.filter(a => a.id !== id)
  setCache(QUEUE_KEY, queue)
}

// 触发队列同步
export async function processQueue() {
  const queue = getQueue()
  if (queue.length === 0) return

  console.log(`[OfflineQueue] 开始同步 ${queue.length} 个离线操作...`)
  const remainingQueue: OfflineAction[] = []

  for (const action of queue) {
    try {
      // 重新发起请求
      await api.request({
        method: action.method,
        url: action.url,
        data: action.data,
        headers: action.headers
      })
      console.log(`[OfflineQueue] 同步成功: ${action.description}`)
    } catch (e: any) {
      // 如果是因为断网或超时，重新放回队列
      if (!e.response || e.code === 'ERR_NETWORK' || e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
        remainingQueue.push(action)
      } 
      // 如果是 409 冲突，说明数据在服务器被其他设备改过了
      else if (e.response?.status === 409) {
        alert(`【同步冲突】你之前离线修改的「${action.description}」无法同步：\n该题目已被其他设备修改。你的离线修改已丢失，请刷新页面获取最新版本。`)
      } 
      // 如果是其他错误（如 401 权限过期），也只能丢弃
      else {
        console.warn(`[OfflineQueue] 同步失败，丢弃: ${action.description}`, e)
      }
    }
  }

  setCache(QUEUE_KEY, remainingQueue)
  if (remainingQueue.length === 0) {
    console.log(`[OfflineQueue] 所有离线操作同步完毕！`)
    // 触发一个事件，通知 UI 刷新
    window.dispatchEvent(new Event('offline-queue-synced'))
  }
}

// 全局监听网络恢复
export function initOfflineQueue() {
  window.addEventListener('online', () => {
    console.log('[Network] 网络恢复，检查离线队列...')
    processQueue()
  })
}