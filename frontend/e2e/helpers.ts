import { expect, type Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export const ADMIN_KEY = process.env.E2E_ADMIN_KEY || 'e2e-key-change-me'
export const DEFAULT_PASSWORD = 'Passw0rd!'

let seq = 0

function uniqueSuffix(): string {
  seq += 1
  return `${Date.now()}${seq}`
}

export function uniqueName(prefix: string): string {
  return `${prefix}_${uniqueSuffix()}`
}

export function uniqueEmail(): string {
  return `e2e${uniqueSuffix()}@example.com`
}

function feedbackLocator(page: Page) {
  return page.locator(
    '.oj-toast, .toast, [role="status"], [role="alert"], .error, .error-text, .success'
  )
}

export async function expectToast(page: Page, pattern: string | RegExp, timeout = 15_000) {
  await expect(feedbackLocator(page).filter({ hasText: pattern }).first()).toBeVisible({ timeout })
}

/**
 * 安装一个统一的 dialog 处理器。
 * - accept=true：确认（删除等）
 * - accept=false：取消；但匹配 expectPattern 的提示类 alert 仍记录
 * 返回收集到的消息数组，便于后续断言。
 */
export function installDialogHandler(
  page: Page,
  options: { accept?: (msg: string) => boolean } = {}
) {
  const messages: string[] = []
  const accept = options.accept || (() => true)

  page.on('dialog', async (dialog) => {
    const msg = dialog.message()
    messages.push(msg)
    try {
      if (accept(msg)) await dialog.accept()
      else await dialog.dismiss()
    } catch {
      // 已被其他处理器处理，忽略
    }
  })

  return messages
}

export async function readUserRole(page: Page): Promise<string | null> {
  return page.evaluate(() => {
    try {
      const raw = localStorage.getItem('oj_user')
      return raw ? (JSON.parse(raw).role as string) : null
    } catch {
      return null
    }
  })
}

export async function ensureAdmin(page: Page): Promise<void> {
  await page.goto('/#/')

  const role = await readUserRole(page)
  if (role !== 'admin') {
    throw new Error(
      `当前会话角色是 ${role || '未登录'}，期望 admin。\n` +
        `若测试库被污染，请执行：\n` +
        `docker compose -f docker-compose.test.yml down -v\n` +
        `docker compose -f docker-compose.test.yml up -d`
    )
  }

  await page.evaluate((key: string) => localStorage.setItem('admin_key', key), ADMIN_KEY)
}

export async function registerRegularUser(
  page: Page
): Promise<{ username: string; password: string }> {
  const username = uniqueName('e2euser')
  const password = DEFAULT_PASSWORD

  await page.goto('/#/register')
  await page.locator('#reg-username').fill(username)
  await page.locator('#reg-email').fill(uniqueEmail())
  await page.locator('#reg-password').fill(password)
  await page.getByRole('button', { name: /注\s*册/ }).click()
  await page.waitForURL(/#\/(?!register|login)/, { timeout: 30_000 })

  return { username, password }
}

/** 创建一道题目，返回标题。以「URL 回到首页」作为成功信号 */
export async function createProblem(
  page: Page,
  overrides: { title?: string; description?: string } = {}
): Promise<string> {
  const title = overrides.title || uniqueName('e2eproblem')
  const description = overrides.description || '这是 E2E 自动创建的题目描述'

  const dialogs = installDialogHandler(page, { accept: () => true })

  await page.goto('/#/admin/problem/new')
  await page.getByPlaceholder('请输入题目标题').fill(title)
  await page.locator('textarea').first().fill(description)
  await page.getByRole('button', { name: '保存' }).click()

  try {
    await page.waitForURL(/#\/$/, { timeout: 20_000 })
  } catch (e) {
    const err = await page
      .locator('.error, .error-text')
      .first()
      .textContent()
      .catch(() => null)
    throw new Error(
      `创建题目失败（title=${title}）：表单错误=${err || '无'}；弹窗=${dialogs.join(' | ') || '无'}`
    )
  }

  page.removeAllListeners('dialog')

  return title
}

export async function openProblemForm(
  page: Page,
  title: string,
  description = '离线用例描述'
): Promise<void> {
  await page.goto('/#/admin/problem/new')
  await page.getByPlaceholder('请输入题目标题').fill(title)
  await page.locator('textarea').first().fill(description)
}

export function readAdminCredentials(): { username: string; password: string } {
  const file = path.join(__dirname, '.auth', 'admin-credentials.json')
  return JSON.parse(fs.readFileSync(file, 'utf-8'))
}