const PREFIX = 'oj_cache_'

export function setCache(key: string, data: any) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify({ savedAt: Date.now(), data }))
    return true
  } catch (e) {
    console.warn('写入缓存失败', e)
    return false
  }
}

export function getCache<T>(key: string): T | null {
  const entry = getCacheEntry<T>(key)
  return entry ? entry.data : null
}

export function getCacheEntry<T>(key: string): { savedAt: number; data: T } | null {
  try {
    const raw = localStorage.getItem(PREFIX + key)
    if (!raw) return null
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object' || !('data' in parsed)) return null
    return parsed as { savedAt: number; data: T }
  } catch (e) {
    return null
  }
}

export function hasCache(key: string): boolean {
  return getCacheEntry(key) !== null
}

export function clearCache(key: string) {
  try {
    localStorage.removeItem(PREFIX + key)
  } catch (e) {}
}

export function clearAllCache() {
  try {
    Object.keys(localStorage)
      .filter(k => k.startsWith(PREFIX))
      .forEach(k => localStorage.removeItem(k))
  } catch (e) {}
}