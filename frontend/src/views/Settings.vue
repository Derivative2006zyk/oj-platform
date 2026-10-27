<template>
  <main class="settings-page">
    <div class="container">
      <header class="page-header">
        <h1>设置</h1>
        <p class="page-desc">配置应用连接与网络</p>
      </header>

      <!-- ===== 后端连接 ===== -->
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

      <!-- ===== 数据备份与恢复 ===== -->
      <section class="card" style="margin-top: var(--spacing-lg);">
        <div class="card-header">
          <span>数据备份与恢复</span>
        </div>
        <div class="card-body">
          <p class="hint">
            导出包含所有题库、账号和上传图片的完整 ZIP 包。恢复操作会覆盖当前所有数据，请谨慎操作。
          </p>
          
          <div class="actions">
            <button class="btn-primary" @click="onBackup" :disabled="backingUp">
              {{ backingUp ? '备份中...' : '导出备份' }}
            </button>
            <button 
              class="btn-ghost" 
              style="color: var(--color-danger-text); border-color: var(--color-danger-text);" 
              @click="onRestoreClick" 
              :disabled="restoring"
            >
              {{ restoring ? '恢复中...' : '从备份恢复' }}
            </button>
            <input
              ref="fileInputRef"
              type="file"
              accept=".zip"
              style="display: none;"
              @change="onRestoreFileChange"
            />
          </div>
        </div>
      </section>

      <!-- ===== 已安装插件 ===== -->
      <section class="card" style="margin-top: var(--spacing-lg);">
        <div class="card-header">
          <span>已安装的扩展插件</span>
        </div>
        <div class="card-body">
          <div v-if="pluginStore.plugins.length === 0" class="empty-text">
            暂无已安装的外部插件。
          </div>
          <div v-else class="plugin-list">
            <div v-for="p in pluginStore.plugins" :key="p.name" class="plugin-item">
              <div class="plugin-info">
                <div class="plugin-title">
                  {{ p.display_name }} <span class="version">v{{ p.version }}</span>
                </div>
                <div class="plugin-desc">{{ p.description }}</div>
                <div class="plugin-author">作者: {{ p.author }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 插件市场 ===== -->
      <section class="card" style="margin-top: var(--spacing-lg);">
        <div class="card-header">
          <span>插件市场</span>
        </div>
        <div class="card-body">
          <div v-if="marketLoading" class="empty-text">
            正在获取市场列表...
          </div>
          <div v-else-if="marketPlugins.length === 0" class="empty-text">
            暂无可用插件。
          </div>
          <div v-else class="plugin-list">
            <div v-for="p in marketPlugins" :key="p.name" class="plugin-item">
              <div class="plugin-info">
                <div class="plugin-title">
                  {{ p.display_name }} <span class="version">v{{ p.version }}</span>
                </div>
                <div class="plugin-desc">{{ p.description }}</div>
                <div class="plugin-author">作者: {{ p.author }}</div>
              </div>
              <button 
                class="btn-primary install-btn" 
                @click="onInstallPlugin(p)"
                :disabled="installing || restarting || !p.download_url"
              >
                {{ installing ? '安装中...' : (p.download_url ? '一键安装' : '敬请期待') }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- ===== 重启全屏遮罩 ===== -->
    <div v-if="restarting" class="restart-overlay">
      <div class="spinner"></div>
      <div class="restart-text">正在重启服务并加载新插件（已耗时 {{ restartSeconds }} 秒）...</div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { invoke } from '@tauri-apps/api/core'
import { getBackendUrl, setBackendUrl, isTauriEnv } from '../utils/backend-url'
import { usePluginStore } from '../stores/plugin'
import api from '../utils/axios'

const router = useRouter()
const pluginStore = usePluginStore()
const isTauri = isTauriEnv()

// ===== 数据备份与恢复 =====
const backingUp = ref(false)
const restoring = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

async function onBackup() {
  backingUp.value = true
  try {
    const adminKey = localStorage.getItem('admin_key') || ''
    const res = await api.get('/admin/backup/export', {
      headers: { 'X-Admin-Key': adminKey },
      responseType: 'blob'
    })
    
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `oj_backup_${Date.now()}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e: any) {
    alert('导出失败：' + (e.response?.data?.detail || e.message))
  } finally {
    backingUp.value = false
  }
}

function onRestoreClick() {
  if (confirm('警告：恢复数据会覆盖当前所有的题库、账号和提交记录！\n\n确定要继续吗？')) {
    fileInputRef.value?.click()
  }
}

async function onRestoreFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const file = input.files[0]
  
  restoring.value = true
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const adminKey = localStorage.getItem('admin_key') || ''
    await api.post('/admin/backup/import', formData, {
      headers: { 
        'X-Admin-Key': adminKey,
        'Content-Type': 'multipart/form-data'
      }
    })
    alert('恢复成功！建议重启软件以确保数据完全同步。')
    window.location.reload()
  } catch (e: any) {
    alert('恢复失败：' + (e.response?.data?.detail || e.message))
  } finally {
    restoring.value = false
    input.value = ''
  }
}

// ===== 网络配置 =====
const currentUrl = ref('')
const inputUrl = ref('')
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

// ===== 插件市场 =====
const marketLoading = ref(true)
const marketPlugins = ref<any[]>([])

async function fetchMarket() {
  marketLoading.value = true
  try {
    const res = await api.get('/market/plugins')
    marketPlugins.value = res.data
  } catch (e) {
    console.error('获取市场列表失败', e)
  } finally {
    marketLoading.value = false
  }
}

// ===== 插件安装与重启 =====
const installing = ref(false)
const restarting = ref(false)
const restartSeconds = ref(0)
let timer: number | null = null

async function onInstallPlugin(plugin: any) {
  if (!plugin.download_url) return
  if (!confirm(`确定要安装 ${plugin.display_name} 吗？`)) return
  
  installing.value = true
  try {
    const adminKey = localStorage.getItem('admin_key') || ''
    
    // 动态使用市场返回的 URL
    await api.post('/admin/market/install', 
      { download_url: plugin.download_url },
      { headers: { 'X-Admin-Key': adminKey } }
    )
    
    if (isTauri) {
      restarting.value = true
      restartSeconds.value = 0
      timer = window.setInterval(() => { restartSeconds.value++ }, 1000)
      
      await invoke('restart_backend_cmd')
      
      let retries = 30
      let ready = false
      
      while (retries > 0 && !ready) {
        try {
          const res = await api.get('/plugins/ui')
          if (res.status === 200) {
            pluginStore.plugins = res.data
            ready = true
          }
        } catch (e) {
          await new Promise(r => setTimeout(r, 500))
          retries--
        }
      }
      
      if (timer) clearInterval(timer)
      restarting.value = false
      installing.value = false
      
      if (ready) {
        alert('插件安装成功，导航栏已更新！')
      } else {
        alert('安装可能超时，请手动刷新页面查看。')
      }
    } else {
      alert('插件安装成功！请手动重启后端服务后刷新页面。')
    }
  } catch (e: any) {
    alert('安装失败：' + (e.response?.data?.detail || e.message || e))
  } finally {
    installing.value = false
    restarting.value = false
    if (timer) clearInterval(timer)
  }
}

onMounted(async () => {
  loadConfig()
  pluginStore.fetchPlugins()
  fetchMarket() // 新增：拉取市场列表
  
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
/* 样式保持完全不变 */
.settings-page {
  padding: var(--spacing-xl) 0;
  min-height: calc(100vh - 56px);
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
.btn-primary, 
.btn-ghost {
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
.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
.btn-primary:disabled {
  background: var(--color-primary-disabled);
  cursor: not-allowed;
}
.btn-ghost {
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}
.btn-ghost:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}
.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
.empty-text {
  text-align: center;
  color: var(--color-text-muted);
  padding: 20px;
  font-size: var(--font-size-body);
}
.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.plugin-item {
  padding: 12px 16px;
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}
.plugin-info {
  flex: 1;
}
.plugin-title {
  font-weight: bold;
  font-size: 15px;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}
.version {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: normal;
  margin-left: 6px;
}
.plugin-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}
.plugin-author {
  font-size: 12px;
  color: var(--color-text-muted);
}
.install-btn {
  margin-left: auto;
  flex-shrink: 0;
}
.restart-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.restart-text {
  margin-top: var(--spacing-md);
  color: var(--color-primary);
  font-weight: bold;
  font-size: var(--font-size-body);
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>