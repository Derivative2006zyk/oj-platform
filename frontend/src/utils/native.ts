import { Capacitor } from '@capacitor/core'
import { Preferences } from '@capacitor/preferences'

const TOKEN_KEY = 'oj_token'

export function isNative(): boolean {
  return Capacitor.isNativePlatform()
}

export async function syncTokenToNative(token: string): Promise<void> {
  if (!isNative()) return
  try {
    await Preferences.set({ key: TOKEN_KEY, value: token })
  } catch {
    // 静默失败
  }
}

export async function clearTokenFromNative(): Promise<void> {
  if (!isNative()) return
  try {
    await Preferences.remove({ key: TOKEN_KEY })
  } catch {
    // 静默失败
  }
}

export async function syncTokenFromLocalStorage(): Promise<void> {
  if (!isNative()) return
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    await syncTokenToNative(token)
  }
}