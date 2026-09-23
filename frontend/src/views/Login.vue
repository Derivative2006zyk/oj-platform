<template>
  <div class="auth-page">
    <div class="auth-box">
      <h1>登录</h1>

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

        <button type="submit" :disabled="loading">
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

    // 登录成功，跳回原页面或首页
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
  min-height: calc(100vh - 60px);
  background: #f5f7fa;
}

.auth-box {
  width: 360px;
  padding: 32px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.auth-box h1 {
  margin: 0 0 24px;
  font-size: 22px;
  text-align: center;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #444;
}

.form-item input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-item input:focus {
  outline: none;
  border-color: #4f46e5;
}

.error {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 13px;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px 0;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

button:disabled {
  background: #a5b4fc;
  cursor: not-allowed;
}

.tip {
  margin-top: 16px;
  font-size: 13px;
  text-align: center;
  color: #666;
}

.tip a {
  color: #4f46e5;
  text-decoration: none;
}
</style>