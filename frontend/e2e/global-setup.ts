import { chromium, type FullConfig } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const AUTH_DIR = path.join(__dirname, '.auth')
const AUTH_FILE = path.join(AUTH_DIR, 'admin.json')
const CRED_FILE = path.join(AUTH_DIR, 'admin-credentials.json')

const ADMIN_KEY = process.env.E2E_ADMIN_KEY || 'e2e-key-change-me'
const PASSWORD = 'Passw0rd!'
const PG_CONTAINER = process.env.E2E_PG_CONTAINER || 'oj-platform-test-postgres-1'
const PG_DB = 'oj_platform_e2e'

/** 通过 docker exec psql 直接提权，避免依赖 JWT 管理接口 */
function promoteToAdmin(username: string) {
  const sql = `UPDATE users SET role='admin' WHERE username='${username}'`
  execFileSync(
    'docker',
    ['exec', PG_CONTAINER, 'psql', '-U', 'oj', '-d', PG_DB, '-c', sql],
    { stdio: 'pipe' }
  )
}

async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0]?.use?.baseURL || 'http://127.0.0.1:5173'

  const browser = await chromium.launch()
  const context = await browser.newContext({ baseURL })
  const page = await context.newPage()

  const stamp = Date.now()
  const username = `e2eadmin${stamp}`
  const email = `e2eadmin${stamp}@example.com`

  await page.goto('/#/register')
  await page.locator('#reg-username').fill(username)
  await page.locator('#reg-email').fill(email)
  await page.locator('#reg-password').fill(PASSWORD)
  await page.getByRole('button', { name: /注\s*册/ }).click()

  try {
    await page.waitForURL(/#\/(?!register|login)/, { timeout: 30_000 })
  } catch (e) {
    const msg = await page.locator('.error, .error-text').first().textContent().catch(() => null)
    await browser.close()
    throw new Error(`globalSetup 注册账号失败：${msg || '未知错误'}`)
  }

  let role = await page.evaluate(() => {
    try {
      const raw = localStorage.getItem('oj_user')
      return raw ? (JSON.parse(raw).role as string) : null
    } catch {
      return null
    }
  })

  // 库非空时首个用户不是 admin：直接改库后重新登录刷新角色
  if (role !== 'admin') {
    console.log(`[globalSetup] ${username} 角色为 ${role}，通过数据库提权…`)
    promoteToAdmin(username)

    await page.evaluate(() => localStorage.clear())
    await page.goto('/#/login')
    await page.locator('input[type="text"]').first().fill(username)
    await page.locator('input[type="password"]').first().fill(PASSWORD)
    await page.getByRole('button', { name: /登\s*录/ }).click()
    await page.waitForURL(/#\/(?!login)/, { timeout: 20_000 })

    role = await page.evaluate(() => {
      const raw = localStorage.getItem('oj_user')
      return raw ? (JSON.parse(raw).role as string) : null
    })
  }

  if (role !== 'admin') {
    await browser.close()
    throw new Error(
      `globalSetup 提权后角色仍为 ${role}。请确认：\n` +
        `1. 测试栈已启动：docker compose -f docker-compose.test.yml up -d\n` +
        `2. 容器名正确：docker ps --format "{{.Names}}" | findstr test-postgres\n` +
        `3. 或执行 down -v 重建空库`
    )
  }

  await page.evaluate((key: string) => localStorage.setItem('admin_key', key), ADMIN_KEY)

  fs.mkdirSync(AUTH_DIR, { recursive: true })
  await context.storageState({ path: AUTH_FILE })
  fs.writeFileSync(CRED_FILE, JSON.stringify({ username, password: PASSWORD }, null, 2))

  console.log(`[globalSetup] 管理员就绪：${username}`)

  await browser.close()
}

export default globalSetup