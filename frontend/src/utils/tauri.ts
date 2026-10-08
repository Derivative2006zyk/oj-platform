/**
 * 判断是否运行在 Tauri 环境。
 * 浏览器中打开时无 __TAURI_INTERNALS__。
 */
export function isTauri(): boolean {
  return typeof window !== 'undefined' && !!(window as any).__TAURI_INTERNALS__
}

/**
 * 调用 Tauri 命令刷新托盘 tooltip。
 * 非 Tauri 环境静默返回。
 */
export async function refreshTrayFromBackend(token: string): Promise<void> {
  if (!isTauri()) return

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('refresh_tray_from_backend', { token })
  } catch (e) {
    console.warn('[tauri] refresh tray failed', e)
  }
}

/**
 * 直接更新 tooltip 文本。
 */
export async function updateTrayTooltip(text: string): Promise<void> {
  if (!isTauri()) return

  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('update_tray_tooltip', { text })
  } catch (e) {
    console.warn('[tauri] update tooltip failed', e)
  }
}