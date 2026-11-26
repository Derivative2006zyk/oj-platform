import { test, expect } from '@playwright/test'
import { ensureAdmin, createProblem } from './helpers'

test.describe('题目详情', () => {
  test.beforeEach(async ({ page }) => {
    await ensureAdmin(page)
  })

  test('详情页正常渲染标题与描述', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    await page.locator('.problem-row', { hasText: title }).first().click()
    await page.waitForURL(/problem\/\d+/, { timeout: 15_000 })

    await expect(page.getByRole('heading', { name: title }).first()).toBeVisible({ timeout: 15_000 })
    await expect(page.getByText('题目描述').first()).toBeVisible()
  })

  test('代码提交面板存在', async ({ page }) => {
    const title = await createProblem(page)

    await page.goto('/#/')
    await page.locator('.problem-row', { hasText: title }).first().click()
    await page.waitForURL(/problem\/\d+/, { timeout: 15_000 })

    await expect(page.getByText('代码提交')).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: '提交' })).toBeVisible()
  })
})