import { test, expect } from '@playwright/test';

// 每次运行生成唯一的账号，避免冲突
const TEST_USER = 'e2e_tester_' + Date.now();
const TEST_PASSWORD = 'test123456';

test.describe('用户认证流程', () => {
  // 在所有测试执行前，通过 API 注册一个新账号
  test.beforeAll(async ({ request }) => {
    await request.post('http://localhost:8000/api/auth/register', {
      data: {
        username: TEST_USER,
        email: `${TEST_USER}@example.com`,
        password: TEST_PASSWORD
      }
    });
  });

  test('新注册的用户能够成功登录', async ({ page }) => {
    await page.goto('/login');
    
    // 使用刚才注册的账号登录
    await page.fill('input[type="text"]', TEST_USER);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    // 期望成功跳回首页
    await expect(page).toHaveURL('/');
  });
});