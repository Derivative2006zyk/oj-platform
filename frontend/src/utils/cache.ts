export function setCache(key: string, data: any) {
  try {
    localStorage.setItem(key, JSON.stringify(data))
  } catch (e) {
    console.warn('写入缓存失败', e)
  }
}

export function getCache<T>(key: string): T | null {
  try {
    const val = localStorage.getItem(key)
    return val ? JSON.parse(val) : null
  } catch (e) {
    return null
  }
}