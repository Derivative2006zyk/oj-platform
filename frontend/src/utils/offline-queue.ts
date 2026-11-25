import { getCache } from './cache'

export type QueuedStatus = 'pending' | 'conflict' | 'dead'

export interface OfflineAction {
  id: string
  method: 'post' | 'put' | 'delete'
  url: string
  data?: any
  headers?: Record<string, string>
  description: string
  createdAt: number
  attempts: number
  lastError?: string
  status: QueuedStatus
}

const QUEUE_KEY = 'oj_offline_queue'
const MAX_ATTEMPTS = 5

// ===== 存储 =====
export function getQueue(): OfflineAction[] {
  const raw = getCache<OfflineAction[]>(QUEUE_KEY)
  if (!Array.isArray(raw)) return []

  return raw
    .filter((a): a is OfflineAction => !!a && typeof a.id === 'string')
    .map(a => ({
      ...a,
      createdAt: typeof a.createdAt === 'number' ? a.createdAt : Date.now(),
      attempts: typeof a.attempts === 'number' ? a.attempts : 0,
      status: a.status || 'pending',
    }))
}

function saveQueue(queue: OfflineAction[]) {
  try {
    localStorage.setItem(
      'oj_cache_' + QUEUE_KEY,
      JSON.stringify({ savedAt: Date.now(), data: queue })
    )
  } catch (e) {
    console.warn('[OfflineQueue] 持久化失败', e)
  }
  window.dispatchEvent(new Event('offline-queue-changed'))
}

function genId() {
  return `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

// ===== 入队 =====
export function enqueueAction(
  input: Omit<OfflineAction, 'id' | 'createdAt' | 'attempts' | 'status'>
): OfflineAction {
  const action: OfflineAction = {
    ...input,
    id: genId(),
    createdAt: Date.now(),
    attempts: 0,
    status: 'pending',
  }

  const queue = getQueue()
  queue.push(action)
  saveQueue(queue)

  console.log(`[OfflineQueue] 已加入队列: ${action.description}`)
  return action
}

// ===== 移除 / 状态变更 =====
export function removeActionFromQueue(id: string) {
  saveQueue(getQueue().filter(a => a.id !== id))
}

export function updateAction(id: string, patch: Partial<OfflineAction>) {
  saveQueue(getQueue().map(a => (a.id === id ? { ...a, ...patch } : a)))
}

export function clearDeadActions() {
  saveQueue(getQueue().filter(a => a.status !== 'dead'))
}

export function clearAllActions() {
  saveQueue([])
}

export function getPendingCount(): number {
  return getQueue().filter(a => a.status === 'pending' || a.status === 'conflict').length
}

export function getDeadCount(): number {
  return getQueue().filter(a => a.status === 'dead').length
}

// ===== 分类：哪些写操作可以入队 =====
export function shouldQueue(method: string, url: string): boolean {
  const m = method.toUpperCase()

  if (m === 'DELETE') return false
  if (url.includes('/submissions')) return false
  if (url.includes('/admin/images')) return false
  if (url.includes('/admin/bank/import')) return false
  if (url.includes('/plugins/llm_ocr/parse')) return false
  if (url.includes('/plugins/ai/chat')) return false

  return url.includes('/admin/problems')
}

export function describeAction(method: string, url: string, data?: any): string {
  const m = method.toUpperCase()
  const idMatch = url.match(/\/admin\/problems\/(\d+)/)

  if (idMatch) {
    const verb = m === 'PUT' ? '修改' : m === 'DELETE' ? '删除' : '操作'
    return `${verb}题目 #${idMatch[1]}`
  }

  if (m === 'POST' && url.includes('/admin/problems')) {
    const title = data?.title ? `「${data.title}」` : ''
    return `新建题目${title}`
  }

  return `${m} ${url}`
}

// ===== 回放 =====
let processing = false

export async function processQueue(): Promise<{ synced: number; failed: number }> {
  if (processing) return { synced: 0, failed: 0 }

  const queue = getQueue().filter(a => a.status === 'pending')
  if (queue.length === 0) return { synced: 0, failed: 0 }

  processing = true
  let synced = 0
  let failed = 0

  console.log(`[OfflineQueue] 开始同步 ${queue.length} 个离线操作…`)

  for (const action of queue) {
    try {
      const { default: api } = await import('./axios')
      await api.request({
        method: action.method,
        url: action.url,
        data: action.data,
        headers: action.headers,
      })

      removeActionFromQueue(action.id)
      synced += 1
      console.log(`[OfflineQueue] 同步成功: ${action.description}`)
    } catch (e: any) {
      const status = e?.response?.status

      // 仍然断网：计数后保留，下轮再试
      if (!e.response || e.code === 'ERR_NETWORK' || e.message?.includes('timeout')) {
        updateAction(action.id, {
          attempts: action.attempts + 1,
          lastError: '网络不可用',
        })
        failed += 1
        continue
      }

      // 冲突：不自动覆盖，标记等待人工处理
      if (status === 409) {
        updateAction(action.id, {
          status: 'conflict',
          attempts: action.attempts + 1,
          lastError: '内容已被其他设备修改',
        })
        failed += 1
        continue
      }

      // 其他 4xx：参数错误，重试无意义
      if (status && status >= 400 && status < 500) {
        updateAction(action.id, {
          status: 'dead',
          attempts: action.attempts + 1,
          lastError: e?.response?.data?.detail || `请求失败（${status}）`,
        })
        failed += 1
        continue
      }

      // 5xx：计数，超过上限进死信
      const attempts = action.attempts + 1
      updateAction(action.id, {
        attempts,
        status: attempts >= MAX_ATTEMPTS ? 'dead' : 'pending',
        lastError: e?.message || '服务端错误',
      })
      failed += 1
    }
  }

  processing = false

  const remaining = getQueue().filter(a => a.status === 'pending').length
  if (remaining === 0) {
    console.log('[OfflineQueue] 待同步操作已清空')
    window.dispatchEvent(new Event('offline-queue-synced'))
  }

  return { synced, failed }
}

export function retryAction(id: string) {
  updateAction(id, { status: 'pending', attempts: 0, lastError: undefined })
  processQueue()
}
export function getConflictActions(): OfflineAction[] {
  return getQueue().filter(a => a.status === 'conflict')
}

/**
 * 解决冲突项。
 * - server：丢弃本地修改
 * - local：用服务端最新版本号重写后重新入队
 */
export function resolveConflict(id: string, resolution: 'local' | 'server', serverVersion?: number) {
  const action = getQueue().find(a => a.id === id)
  if (!action) return

  if (resolution === 'server') {
    removeActionFromQueue(id)
    return
  }

  updateAction(id, {
    status: 'pending',
    attempts: 0,
    lastError: undefined,
    data: {
      ...(action.data || {}),
      version: typeof serverVersion === 'number' ? serverVersion : (action.data?.version ?? 1),
    },
  })

  processQueue()
}
// ===== 初始化 =====
export function initOfflineQueue() {
  window.addEventListener('online', () => {
    console.log('[Network] 网络恢复，检查离线队列…')
    processQueue()
  })
}