import { test, expect } from '@playwright/test'
import { ensureAdmin, createProblem, installDialogHandler } from './helpers'

test.describe('题库 CRUD', () => {
  test.beforeEach(async ({ page }) => {
    await ensureAdmin(page)
  })

  test('可以创建题目并在列表中看到', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    await expect(page.getByText(title).first()).toBeVisible({ timeout: 15_000 })
  })

  test('可以编辑题目标题', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    const row = page.locator('.problem-row', { hasText: title }).first()
    await expect(row).toBeVisible({ timeout: 15_000 })

    await row.getByRole('button', { name: '编辑' }).click()
    await page.waitForURL(/admin\/problem\/\d+\/edit/, { timeout: 15_000 })

    // 等详情加载完成，确保 form.version 已回填
    await expect(page.getByPlaceholder('请输入题目标题')).toHaveValue(title, { timeout: 15_000 })

    const newTitle = `${title}_edited`
    installDialogHandler(page, { accept: () => true })

    await page.getByPlaceholder('请输入题目标题').fill(newTitle)

    const putPromise = page.waitForResponse(
      (r) => r.url().includes('/admin/problems/') && r.request().method() === 'PUT',
      { timeout: 20_000 }
    )

    await page.getByRole('button', { name: '保存' }).click()

    const res = await putPromise
    const body = await res.text()

    expect(res.status(), `PUT 返回：${body}`).toBeLessThan(400)

    await page.waitForURL(/#\/$/, { timeout: 20_000 })
    await expect(page.getByText(newTitle).first()).toBeVisible({ timeout: 15_000 })
  })

  test('搜索可以过滤列表', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    await page.getByPlaceholder('搜索题目...').fill(title)
    await page.getByRole('button', { name: '搜索' }).click()

    await expect(page.getByText(title).first()).toBeVisible({ timeout: 15_000 })
  })

  test('可以删除题目', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    const row = page.locator('.problem-row', { hasText: title }).first()
    await expect(row).toBeVisible({ timeout: 15_000 })

    // 只接受「删除」确认框
    installDialogHandler(page, {
      accept: (msg) => /确定删除题目/.test(msg),
    })

    await row.getByRole('button', { name: '删除' }).click()

    await expect(page.getByText(title)).toHaveCount(0, { timeout: 20_000 })
  })
})