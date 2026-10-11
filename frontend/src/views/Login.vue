<template>
  <div class="auth-page">
    <div class="card auth-box">
      <header class="auth-header">
        <h1>登录</h1>
        <p class="auth-subtitle">欢迎回到 OJ Platform</p>
      </header>

      <form @submit.prevent="onSubmit">
        <div class="form-item">
          <label>用户名</label>
          <input v-model="form.username" type="text" required />
        </div>

        <div class="form-item">
          <label>密码</label>
          <input v-model="form.password" type="password" required />
        </div>

        <div v-if="error" class="error">{{ error }}</div>

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <p class="tip">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true

  try {
    await userStore.login({
      username: form.username,
      password: form.password,
    })

    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) {
      error.value = '用户名或密码错误'
    } else {
      error.value = e?.response?.data?.detail || '登录失败，请稍后重试'
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