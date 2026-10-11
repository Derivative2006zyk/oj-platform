<template>
  <div class="auth-page">
    <div class="card auth-box">
      <header class="auth-header">
        <h1>注册</h1>
        <p class="auth-subtitle">创建你的 OJ Platform 账号</p>
      </header>

      <form @submit.prevent="onSubmit">
        <div class="form-item">
          <label>用户名</label>
          <input
            v-model="form.username"
            type="text"
            required
            minlength="3"
            maxlength="50"
            placeholder="3-50 个字符"
          />
        </div>

        <div class="form-item">
          <label>邮箱</label>
          <input
            v-model="form.email"
            type="email"
            required
            placeholder="you@example.com"
          />
        </div>

        <div class="form-item">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            required
            minlength="6"
            placeholder="至少 6 位"
          />
        </div>

        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="success" class="success">{{ success }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <p class="tip">
        已有账号？<router-link to="/login">去登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
})

const loading = ref(false)
const error = ref('')
const success = ref('')

async function onSubmit() {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    await userStore.register({
      username: form.username,
      email: form.email,
      password: form.password,
    })

    success.value = '注册成功，即将跳转登录...'

    setTimeout(() => {
      router.push('/login')
    }, 800)
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 409) {
      error.value = '用户名或邮箱已被占用'
    } else if (status === 422) {
      error.value = '输入格式不正确，请检查用户名、邮箱、密码'
    } else {
      error.value = e?.response?.data?.detail || '注册失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 56px);
  padding: var(--spacing-lg);
  background: var(--color-bg-page);
}

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.auth-box {
  width: 100%;
  max-width: 380px;
  padding: var(--spacing-xl);
}

.auth-header {
  margin-bottom: var(--spacing-lg);
  text-align: center;
}

.auth-header h1 {
  margin: 0 0 var(--spacing-xs);
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.auth-subtitle {
  margin: 0;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.form-item {
  margin-bottom: var(--spacing-md);
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.form-item input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-family: inherit;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  box-sizing: border-box;
  outline: none;
  transition: border-color 0.2s;
}

.form-item input:focus {
  border-color: var(--color-primary);
}

.error {
  margin-bottom: var(--spacing-md);
  padding: 10px 12px;
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  font-size: 13px;
  border-radius: var(--radius-md);
}

.success {
  margin-bottom: var(--spacing-md);
  padding: 10px 12px;
  background: var(--color-success-bg);
  color: var(--color-success-text);
  font-size: 13px;
  border-radius: var(--radius-md);
}

.btn-primary {
  width: 100%;
  padding: 10px 0;
  margin-top: var(--spacing-xs);
  background: var(--color-primary);
  color: var(--color-primary-text);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  font-family: inherit;
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

.tip {
  margin: var(--spacing-lg) 0 0;
  font-size: var(--font-size-small);
  text-align: center;
  color: var(--color-text-secondary);
}

.tip a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.tip a:hover {
  text-decoration: underline;
}
</style>