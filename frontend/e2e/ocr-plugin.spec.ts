import { test, expect } from '@playwright/test'
import { ensureAdmin } from './helpers'

test.describe('AI 拍照录题插件', () => {
  test('插件页可以打开并注入登录上下文', async ({ page }) => {
    await ensureAdmin(page)
    await page.goto('/#/plugin/llm_ocr_plugin')

    const frame = page.frameLocator('iframe.plugin-iframe')

    await expect(frame.locator('#workspace')).toBeVisible({ timeout: 30_000 })
    await expect(frame.getByRole('button', { name: '拍照' })).toBeVisible()
  })

  test('未登录时插件页显示登录引导', async ({ page }) => {
    // 第一步：进入应用并清空登录态
    await page.goto('/#/')
    await page.evaluate(() => localStorage.clear())

    // 第二步：整页刷新，确保 Pinia 从空 localStorage 重新初始化
    await page.reload()
    await page.waitForLoadState('networkidle')

    // 第三步：直接打开插件路由（带 noauth），让浏览器做完整导航
    await page.goto('/#/plugin/llm_ocr_plugin?noauth=1')

    const iframe = page.locator('iframe.plugin-iframe')
    await expect(iframe).toBeVisible({ timeout: 30_000 })

    const src = await iframe.getAttribute('src')
    expect(src, `iframe src 应包含 noauth=1，实际：${src}`).toContain('noauth=1')

    const frame = page.frameLocator('iframe.plugin-iframe')

    await expect(frame.locator('#authGate')).toBeVisible({ timeout: 30_000 })
    await expect(frame.getByRole('button', { name: '前往登录' })).toBeVisible()
    await expect(frame.locator('#workspace')).toBeHidden()
  })
})