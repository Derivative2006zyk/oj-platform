<template>
  <main class="settings-page">
    <div class="container">
      <header class="page-header">
        <h1>设置</h1>
        <p class="page-desc">配置应用连接与网络</p>
      </header>

      <section class="card">
        <div class="card-header">
          <span>后端连接地址</span>
        </div>
        <div class="card-body">
          <p class="hint">
            当前连接地址：<code>{{ currentUrl || '相对路径 (默认)' }}</code>
          </p>
          
          <div v-if="lanIp && isTauri" class="lan-tip">
            本机局域网地址：<strong>{{ lanIp }}</strong><br>
            (移动端请填入此地址)
          </div>

          <div class="form-item">
            <label>修改后端地址</label>
            <input
              v-model="inputUrl"
              type="text"
              placeholder="例如: http://192.168.1.100:8000"
            />
            <small class="help">留空则默认连接本机或相对路径</small>
          </div>

          <div class="actions">
            <button class="btn-primary" @click="saveConfig">保存</button>
            <button class="btn-ghost" @click="testConnection" :disabled="testing">
              {{ testing ? '测试中...' : '测试连接' }}
            </button>
            <button class="btn-ghost" @click="resetConfig">重置默认</button>
          </div>

          <div v-if="testResult" :class="['test-result', testSuccess ? 'success' : 'error']">
            {{ testResult }}
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { getBackendUrl, setBackendUrl, isTauriEnv } from '../utils/backend-url'

const currentUrl = ref('')
const inputUrl = ref('')
const isTauri = isTauriEnv()
const lanIp = ref('')

const testing = ref(false)
const testResult = ref('')
const testSuccess = ref(false)

function loadConfig() {
  currentUrl.value = getBackendUrl()
  inputUrl.value = currentUrl.value
}

function saveConfig() {
  setBackendUrl(inputUrl.value)
  currentUrl.value = getBackendUrl()
  alert('保存成功！')
  // 保存后自动刷新页面，让 axios 重新读取 baseURL，并回到首页/登录页
  window.location.href = '/'
}

function resetConfig() {
  setBackendUrl('')
  loadConfig()
}

async function testConnection() {
  testing.value = true
  testResult.value = ''
  
  const base = inputUrl.value.trim().replace(/\/$/, '') || (isTauri ? 'http://127.0.0.1:8000' : '')
  
  const targetUrl = base ? `${base}/health` : '/health'
  
  try {
    const start = Date.now()
    const res = await fetch(targetUrl, { 
      method: 'GET',
      mode: 'cors',
      headers: { 'Accept': 'application/json' }
    })
    const duration = Date.now() - start
    
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'ok') {
        testSuccess.value = true
        testResult.value = `连接成功！耗时 ${duration}ms。Redis 状态：${data.redis}`
      } else {
        testSuccess.value = false
        testResult.value = '响应格式异常'
      }
    } else {
      testSuccess.value = false
      testResult.value = `HTTP 错误：${res.status}`
    }
  } catch (e: any) {
    testSuccess.value = false
    testResult.value = `连接失败：${e.message || e}`
  } finally {
    testing.value = false
  }
}

onMounted(async () => {
  loadConfig()
  if (isTauri) {
    try {
      lanIp.value = await invoke<string>('get_lan_ip')
    } catch (e) {
      console.warn('获取局域网 IP 失败', e)
    }
  }
})
</script>

<style scoped>
.settings-page {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs);
}

.page-desc {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
}

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.card-header {
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-small);
}

.card-body {
  padding: var(--spacing-lg);
}

.hint {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.hint code {
  background: var(--color-sample-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

.lan-tip {
  background: var(--color-primary-light);
  color: var(--color-primary);
  padding: 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  margin-bottom: var(--spacing-lg);
  line-height: 1.6;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: var(--spacing-lg);
}

.form-item label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.form-item input {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  outline: none;
}

.form-item input:focus {
  border-color: var(--color-primary);
}

.help {
  font-size: 12px;
  color: var(--color-text-muted);
}

.actions {
  display: flex;
  gap: var(--spacing-sm);
}

.btn-primary, .btn-ghost {
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-ghost:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.test-result {
  margin-top: var(--spacing-md);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
}

.test-result.success {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.test-result.error {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}
</style>