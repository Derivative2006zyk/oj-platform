import { ref } from 'vue'
import { getBackendUrl } from './backend-url'

export type ConnState = 'checking' | 'online' | 'offline'

const state = ref<ConnState>('checking')
const lastCheckedAt = ref(0)

let probing: Promise<boolean> | null = null

export function useConnectivity() {
  return { state, lastCheckedAt, probe }
}

export function getConnState() {
  return state.value
}

export function probe(timeoutMs = 6000): Promise<boolean> {
  if (probing) return probing

  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    state.value = 'offline'
    lastCheckedAt.value = Date.now()
    return Promise.resolve(false)
  }

  const base = getBackendUrl()
  const controller = new AbortController()

  void setTimeout(() => controller.abort(), timeoutMs)

  probing = fetch(`${base}/health`, { cache: 'no-store', signal: controller.signal })
    .then(res => res.ok)
    .catch(() => false)
    .then(ok => {
      state.value = ok ? 'online' : 'offline'
      lastCheckedAt.value = Date.now()
      probing = null
      return ok
    })

  return probing
}

export function markOffline() {
  state.value = 'offline'
  lastCheckedAt.value = Date.now()
}

export function markOnline() {
  state.value = 'online'
  lastCheckedAt.value = Date.now()
}