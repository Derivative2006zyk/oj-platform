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
          <div class="plugin-item">
            <div class="plugin-info">
              <div class="plugin-title">示例插件 (Hello World)</div>
              <div class="plugin-desc">这是一个演示用的插件，安装后会在导航栏多出一个菜单。</div>
              <div class="plugin-author">作者: OJ Team | v0.1.0</div>
            </div>
            <button class="btn-primary install-btn" @click="onInstallTest" :disabled="installing">
              {{ installing ? '安装中...' : '一键安装' }}
            </button>
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
import { usePluginStore } from '../stores/plugin'
import api from '../utils/axios'

const pluginStore = usePluginStore()

const backingUp = ref(false)
const restoring = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

// ===== 备份与恢复 =====
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

// ===== 网络连接配置 =====
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

// ===== 插件市场安装 =====
const installing = ref(false)

async function onInstallTest() {
  if (!confirm('确定要安装该插件吗？安装完成后需要重启后端。')) return
  installing.value = true
  try {
    const adminKey = localStorage.getItem('admin_key') || ''
    // 测试用的本地服务器地址
    const downloadUrl = "http://host.docker.internal:9000/hello_world.zip"
    
    const res = await api.post('/admin/market/install', 
      { download_url: downloadUrl },
      { headers: { 'X-Admin-Key': adminKey } }
    )
    alert(res.data.message)
  } catch (e: any) {
    alert('安装失败：' + (e.response?.data?.detail || e.message))
  } finally {
    installing.value = false
  }
}

onMounted(async () => {
  loadConfig()
  pluginStore.fetchPlugins()
  
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

/* ===== 卡片基础 ===== */
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

/* ===== 表单与按钮 ===== */
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

/* ===== 状态提示 ===== */
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

/* ===== 插件列表与市场 ===== */
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
</style>