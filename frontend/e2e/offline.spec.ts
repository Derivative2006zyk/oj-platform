import { test, expect } from '@playwright/test'
import { ensureAdmin, uniqueName, openProblemForm, installDialogHandler } from './helpers'

test.describe('离线优先', () => {
  test.beforeEach(async ({ page }) => {
    await ensureAdmin(page)
    await page.goto('/#/')
    await expect(page.getByRole('heading', { name: '题库', exact: true })).toBeVisible({
      timeout: 15_000,
    })
  })

  /** 真正拦截 write 请求，模拟断网（同时使 navigator.onLine 保持可用） */
  async function blockWriteApi(context: import('@playwright/test').BrowserContext) {
    await context.route('**/api/**', (route) => {
      const method = route.request().method()
      if (method === 'GET') return route.continue()
      return route.abort('internetdisconnected')
    })
  }

  test('断网后提交录入进入本地队列', async ({ page, context }) => {
    const title = uniqueName('e2eoffline')

    await openProblemForm(page, title)
    await blockWriteApi(context)

    const dialogs = installDialogHandler(page, { accept: () => true })
    await page.getByRole('button', { name: '保存' }).click()

    await page.waitForURL(/#\/$/, { timeout: 20_000 })

    const raw = await page.evaluate(() => localStorage.getItem('oj_cache_oj_offline_queue'))
    expect(raw).toBeTruthy()
    expect(raw).toContain(title)
    expect(dialogs.join(' ')).toMatch(/队列|离线|已保存/)
  })

  test('断网时删除失败且页面不崩', async ({ page, context }) => {
    await page.goto('/#/')

    const dialogs = installDialogHandler(page, { accept: () => true })
    await blockWriteApi(context)

    const deleteBtn = page.getByRole('button', { name: '删除' }).first()
    if (await deleteBtn.count()) {
      await deleteBtn.click()
      await expect
        .poll(() => dialogs.join(' | '), { timeout: 15_000 })
        .toMatch(/删除失败|需要联网|离线/)
    }

    // 页面仍然可用
    await expect(page.getByRole('heading', { name: '题库', exact: true })).toBeVisible()
  })

  test('离线队列在 Local Storage 中持久化', async ({ page, context }) => {
    const title = uniqueName('e2epersist')

    await openProblemForm(page, title)
    await blockWriteApi(context)

    installDialogHandler(page, { accept: () => true })
    await page.getByRole('button', { name: '保存' }).click()

    await page.waitForURL(/#\/$/, { timeout: 20_000 })

    const raw = await page.evaluate(() => localStorage.getItem('oj_cache_oj_offline_queue'))
    expect(raw).toBeTruthy()
    expect(raw).toContain('pending')
  })
})