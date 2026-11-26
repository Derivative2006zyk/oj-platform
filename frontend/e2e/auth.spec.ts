import { test, expect } from '@playwright/test'
import { uniqueName, uniqueEmail, DEFAULT_PASSWORD, expectToast } from './helpers'

test.describe('认证', () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  async function registerFresh(page: import('@playwright/test').Page, name: string) {
    await page.goto('/#/register')
    await page.locator('#reg-username').fill(name)
    await page.locator('#reg-email').fill(uniqueEmail())
    await page.locator('#reg-password').fill(DEFAULT_PASSWORD)
    await page.getByRole('button', { name: /注\s*册/ }).click()
    await page.waitForURL(/#\/(?!register|login)/, { timeout: 30_000 })
  }

  test('新注册用户可进入个人中心', async ({ page }) => {
    const name = uniqueName('e2euser')
    await registerFresh(page, name)

    await page.goto('/#/profile')
    await expect(page.getByText(name).first()).toBeVisible({ timeout: 15_000 })
  })

  test('登出后可重新登录', async ({ page }) => {
    const name = uniqueName('e2euser')
    await registerFresh(page, name)

    await page.getByText('登出').click()

    // NavBar.onLogout 是 router.push('/')，登出后停在首页、导航栏出现「登录」
    await expect(page.getByRole('link', { name: '登录' })).toBeVisible({ timeout: 15_000 })

    await page.goto('/#/login')
    await page.locator('input[type="text"]').first().fill(name)
    await page.locator('input[type="password"]').first().fill(DEFAULT_PASSWORD)
    await page.getByRole('button', { name: /登\s*录/ }).click()

    await page.waitForURL(/#\/(?!login)/, { timeout: 20_000 })
    await expect(page.getByText(name).first()).toBeVisible({ timeout: 15_000 })
  })

  test('错误密码登录被拒绝', async ({ page }) => {
    await page.goto('/#/login')
    await page.locator('input[type="text"]').first().fill('not_exist_user_e2e')
    await page.locator('input[type="password"]').first().fill('wrong_password')
    await page.getByRole('button', { name: /登\s*录/ }).click()

    await expectToast(page, /失败|错误|不存在|密码|Invalid/)
    await expect(page).toHaveURL(/#\/login/)
  })
})