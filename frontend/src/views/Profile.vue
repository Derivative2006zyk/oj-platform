<template>
  <main class="profile-page">
    <div class="container">
      <header class="page-header">
        <h1>个人中心</h1>
      </header>

      <!-- ===== 账号信息 ===== -->
      <section class="card user-card">
        <div class="user-hero">
          <div class="avatar-large">
            {{ (userStore.user?.username || '?').slice(0, 1).toUpperCase() }}
          </div>
          <div class="user-meta">
            <div class="username-row">
              <h2>{{ userStore.user?.username }}</h2>
              <span v-if="userStore.isAdmin" class="role-badge">管理员</span>
              <span v-else class="role-badge user">普通用户</span>
            </div>
            <div class="email-row">{{ userStore.user?.email }}</div>
          </div>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">用户 ID</span>
            <span class="info-value">{{ userStore.user?.id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">注册时间</span>
            <span class="info-value">{{ formatTime(userStore.user?.created_at) }}</span>
          </div>
        </div>
      </section>

      <!-- ===== 统计 ===== -->
      <section class="card">
        <div class="card-header">
          <span>我的统计</span>
        </div>

        <div v-if="statsLoading" class="empty-state">加载中...</div>
        <div v-else-if="stats" class="stats-content">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_submissions }}</div>
              <div class="stat-label">总提交</div>
            </div>
            <div class="stat-card">
              <div class="stat-value success">{{ stats.accepted_submissions }}</div>
              <div class="stat-label">通过数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value primary">{{ stats.solved_problems }}</div>
              <div class="stat-label">已解决题目</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.acceptance_rate }}%</div>
              <div class="stat-label">通过率</div>
            </div>
          </div>

          <div
            v-if="Object.keys(stats.language_distribution).length"
            class="lang-dist"
          >
            <h3>语言分布</h3>
            <div class="lang-bars">
              <div
                v-for="(count, lang) in stats.language_distribution"
                :key="lang"
                class="lang-row"
              >
                <span class="lang-name">{{ lang }}</span>
                <div class="lang-bar-wrap">
                  <div
                    class="lang-bar"
                    :style="{ width: barWidth(count) + '%' }"
                  ></div>
                </div>
                <span class="lang-count">{{ count }} 次</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 修改密码 ===== -->
      <section class="card">
        <div class="card-header">
          <span>修改密码</span>
        </div>
        <div class="password-form">
          <div class="form-item">
            <label>旧密码</label>
            <input
              v-model="pwdForm.old_password"
              type="password"
              placeholder="请输入当前密码"
            />
          </div>
          <div class="form-item">
            <label>新密码</label>
            <input
              v-model="pwdForm.new_password"
              type="password"
              placeholder="至少 6 位"
            />
          </div>
          <div class="form-item">
            <label>确认新密码</label>
            <input
              v-model="pwdForm.confirm"
              type="password"
              placeholder="再次输入新密码"
            />
          </div>
          <div v-if="pwdMsg" :class="['msg', pwdSuccess ? 'msg-success' : 'msg-error']">
            {{ pwdMsg }}
          </div>
          <button
            class="btn-primary"
            :disabled="pwdSubmitting"
            @click="onChangePassword"
          >
            {{ pwdSubmitting ? '提交中...' : '修改密码' }}
          </button>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { getMyStats, changePassword, type UserStats } from '../api/user'

const userStore = useUserStore()

const stats = ref<UserStats | null>(null)
const statsLoading = ref(true)

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})

const pwdSubmitting = ref(false)
const pwdMsg = ref('')
const pwdSuccess = ref(false)

const maxLangCount = computed(() => {
  if (!stats.value) return 1
  const counts = Object.values(stats.value.language_distribution)
  return counts.length ? Math.max(...counts) : 1
})

function barWidth(count: number): number {
  if (maxLangCount.value === 0) return 0
  return Math.max(5, Math.round((count / maxLangCount.value) * 100))
}

function formatTime(s?: string): string {
  if (!s) return '-'
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return s
  }
}

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await getMyStats()
  } catch (e) {
    console.error('加载统计失败', e)
  } finally {
    statsLoading.value = false
  }
}

async function onChangePassword() {
  pwdMsg.value = ''
  pwdSuccess.value = false

  if (!pwdForm.old_password || !pwdForm.new_password) {
    pwdMsg.value = '请填写完整'
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm) {
    pwdMsg.value = '两次输入的新密码不一致'
    return
  }
  if (pwdForm.new_password.length < 6) {
    pwdMsg.value = '新密码至少 6 位'
    return
  }

  pwdSubmitting.value = true

  try {
    await changePassword(pwdForm.old_password, pwdForm.new_password)
    pwdSuccess.value = true
    pwdMsg.value = '密码修改成功'
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
  } catch (e: any) {
    pwdMsg.value = e?.response?.data?.detail || '修改失败'
  } finally {
    pwdSubmitting.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.profile-page {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

/* ===== 卡片基础 ===== */
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-card-hover);
}

.card-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  font-size: var(--font-size-small);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted);
}

/* ===== 用户卡片 ===== */
.user-card {
  padding: var(--spacing-lg);
}

.user-hero {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  padding-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: var(--spacing-lg);
}

.avatar-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0066cc, #3399ff);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.user-meta {
  flex: 1;
  min-width: 0;
}

.username-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.username-row h2 {
  margin: 0;
  font-size: 20px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.role-badge {
  padding: 2px 10px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  font-size: 12px;
  border-radius: 12px;
  font-weight: 500;
}

.role-badge.user {
  background: var(--color-neutral-bg);
  color: var(--color-neutral-text);
}

.email-row {
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  word-break: break-all;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
}

.info-label {
  color: var(--color-text-secondary);
}

.info-value {
  font-weight: 500;
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
}

/* ===== 统计 ===== */
.stats-content {
  padding: var(--spacing-lg);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--spacing-md);
}

.stat-card {
  padding: var(--spacing-md);
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  text-align: center;
  transition: background 0.2s;
}

.stat-card:hover {
  background: #f0f2f5;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
  line-height: 1.2;
}

.stat-value.success {
  color: var(--color-success-text);
}

.stat-value.primary {
  color: var(--color-primary);
}

.stat-label {
  margin-top: 6px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

/* ===== 语言分布 ===== */
.lang-dist {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.lang-dist h3 {
  margin: 0 0 var(--spacing-md);
  font-size: 15px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.lang-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lang-row {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: var(--spacing-md);
  font-size: var(--font-size-body);
}

.lang-name {
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
}

.lang-bar-wrap {
  height: 8px;
  background: var(--color-sample-bg);
  border-radius: 4px;
  overflow: hidden;
}

.lang-bar {
  height: 100%;
  background: linear-gradient(90deg, #0066cc, #3399ff);
  border-radius: 4px;
  transition: width 0.4s ease;
}

.lang-count {
  text-align: right;
  font-family: var(--font-family-mono);
  color: var(--color-text-primary);
}

/* ===== 修改密码 ===== */
.password-form {
  padding: var(--spacing-lg);
  max-width: 480px;
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
}

.form-item input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.2s;
}

.form-item input:focus {
  border-color: var(--color-primary);
}

.btn-primary {
  margin-top: var(--spacing-sm);
  padding: 10px 28px;
  background: var(--color-primary);
  color: var(--color-primary-text);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  background: var(--color-primary-disabled);
  cursor: not-allowed;
}

.msg {
  margin-bottom: var(--spacing-md);
  padding: 10px 14px;
  font-size: 13px;
  border-radius: var(--radius-md);
}

.msg-error {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.msg-success {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

/* ===== 响应式 ===== */
@media (max-width: 600px) {
  .container {
    padding: 0 var(--spacing-md);
  }

  .user-hero {
    flex-direction: column;
    text-align: center;
  }

  .username-row {
    justify-content: center;
  }

  .lang-row {
    grid-template-columns: 60px 1fr 50px;
    gap: var(--spacing-sm);
  }
}
</style>