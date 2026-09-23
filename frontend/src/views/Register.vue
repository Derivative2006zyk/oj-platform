<template>
  <div class="auth-page">
    <div class="auth-box">
      <h1>注册</h1>

      <form @submit.prevent="onSubmit">
        <div class="form-item">
          <label>用户名</label>
          <input
            v-model="form.username"
            type="text"
            required
            minlength="3"
            maxlength="50"
          />
        </div>

        <div class="form-item">
          <label>邮箱</label>
          <input v-model="form.email" type="email" required />
        </div>

        <div class="form-item">
          <label>密码</label>
          <input
            v-model="form.password"
            type="password"
            required
            minlength="6"
          />
        </div>

        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="success" class="success">{{ success }}</div>

        <button type="submit" :disabled="loading">
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

.success {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #ecfdf5;
  color: #047857;
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