<template>
  <div v-if="visible" class="modal-mask" @click.self="close">
    <div class="modal">
      <header class="modal-header">
        <h2>智能拍照录题</h2>
        <button class="modal-close" @click="close">×</button>
      </header>

      <div class="modal-body">
        <!-- 第一步：上传图片 -->
        <div v-if="step === 'upload'" class="upload-area">
          
          <!-- 【新增】识别引擎选择 -->
          <div class="form-group" style="margin-bottom: 12px;">
            <label style="display:block; margin-bottom:8px; font-weight:bold;">识别引擎</label>
            <select v-model="ocrEngine" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ddd;">
              <option value="local">本地 PaddleOCR (免费，适合纯文本)</option>
              <option v-if="hasLlmPlugin" value="llm">云端 AI 视觉 (高精度，公式秒识别)</option>
            </select>
          </div>

          <div class="form-group" style="margin-bottom: 20px;">
            <label style="display:block; margin-bottom:8px; font-weight:bold;">请选择题型</label>
            <select v-model="selectedType" style="width:100%; padding:10px; border-radius:6px; border:1px solid #ddd;">
              <option value="algorithm">算法题</option>
              <option value="choice">选择题</option>
              <option value="fill_blank">填空题</option>
              <option value="proof">证明题</option>
            </select>
          </div>
          
          <input type="file" accept="image/*" capture="environment" style="display: none" ref="fileInputRef" @change="onFileSelected" />
          <div class="upload-box" @click="fileInputRef?.click()">
            <p>点击此处拍照或选择图片</p>
            <small>支持一图多题，公式自动转 LaTeX</small>
          </div>
        </div>

        <!-- 第二步：识别中 -->
        <div v-else-if="step === 'parsing'" class="loading-area">
          <div class="spinner"></div>
          <p>正在识别图片中的题目...</p>
        </div>

        <!-- 第三步：预览与确认 -->
        <div v-else-if="step === 'preview'" class="preview-area">
          <p class="hint">已识别出 {{ parsedProblems.length }} 道题目，请勾选需要导入的题：</p>
          
          <!-- 归属选择区 -->
          <div style="background: var(--color-sample-bg); padding: 12px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--color-border);">
            <div style="display: flex; gap: 12px;">
              <div style="flex: 1;">
                <label style="font-size: 12px; color: var(--color-text-secondary);">归属题库(分组)</label>
                <select v-model="selectedBank" class="filter-select" style="width: 100%; margin-top: 4px;">
                  <option :value="null">不归属</option>
                  <option v-for="b in banks" :key="b.id" :value="b.id">{{ b.name }}</option>
                </select>
              </div>
              <div style="flex: 1;">
                <label style="font-size: 12px; color: var(--color-text-secondary);">归属试卷</label>
                <select v-model="selectedPaper" class="filter-select" style="width: 100%; margin-top: 4px;" :disabled="!selectedBank">
                  <option :value="null">散题</option>
                  <option v-for="p in papers" :key="p.id" :value="p.id">{{ p.name }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="problem-list">
            <label v-for="p in parsedProblems" :key="p.temp_id" class="problem-item">
              <input type="checkbox" v-model="selectedIds" :value="p.temp_id" />
              <div class="problem-content">
                <div class="problem-title">{{ p.title }}</div>
                <div class="problem-desc">{{ p.description.slice(0, 50) }}...</div>
              </div>
            </label>
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button class="btn-ghost" @click="close">取消</button>
        <button v-if="step === 'preview'" class="btn-primary" :disabled="selectedIds.length === 0 || importing" @click="onImport">
          {{ importing ? '导入中...' : `导入选中的 ${selectedIds.length} 道题` }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import api from '../utils/axios'
import { listBanks } from '../api/bank'
import { usePluginStore } from '../stores/plugin'

defineProps<{ visible: boolean }>()
const emit = defineEmits(['close', 'success'])

const pluginStore = usePluginStore()

// 【新增】动态判断云端视觉插件是否已安装并启用
const hasLlmPlugin = computed(() => {
  const p = pluginStore.plugins.find(x => x.name === 'llm_ocr_plugin')
  return p && p.enabled !== false
})

const step = ref<'upload' | 'parsing' | 'preview'>('upload')
const fileInputRef = ref<HTMLInputElement | null>(null)
const parsedProblems = ref<any[]>([])
const selectedIds = ref<string[]>([])
const importing = ref(false)
const selectedType = ref('algorithm')

// 【新增】默认引擎逻辑
const ocrEngine = ref<'local' | 'llm'>('local')
watch(hasLlmPlugin, (val) => {
  if (val) ocrEngine.value = 'llm'
}, { immediate: true })

// 试卷与分组数据
const banks = ref<any[]>([])
const papers = ref<any[]>([])
const selectedBank = ref<number | null>(null)
const selectedPaper = ref<number | null>(null)

onMounted(async () => {
  try {
    const res = await listBanks()
    banks.value = res
  } catch (e) { console.error(e) }
})

// 监听题库变化，拉取试卷
watch(selectedBank, async (newVal) => {
  selectedPaper.value = null
  if (!newVal) { papers.value = []; return }
  try {
    const res = await api.get(`/papers?bank_id=${newVal}`)
    papers.value = res.data
  } catch (e) { console.error(e) }
})

function close() {
  if (step.value === 'parsing') return
  step.value = 'upload'
  parsedProblems.value = []
  selectedIds.value = []
  selectedBank.value = null
  selectedPaper.value = null
  emit('close')
}

function formatLatex(text: string) {
  if (!text) return text
  let result = text
  
  // 1. 替换公式定界符
  result = result.replace(/\\\[([\s\S]*?)\\\]/g, '$$\n$1\n$$')
  result = result.replace(/\\\(([\s\S]*?)\\\)/g, '$$$1$$')
  result = result.replace(/\\\\/g, '\\')
  
  // 2. 修复各种绝对值符号
  result = result.replace(/\\lvert/g, '|')
  result = result.replace(/\\rvert/g, '|')
  result = result.replace(/\\vert/g, '|')
  result = result.replace(/\\mid/g, '|')
  
  // 3. 【关键修复】统一极限语法。绝对不能用 \lim_\limits，必须用 \lim\limits_
  // 把所有 \lim_、\lim_\limits_、\lim\limits_ 统一强行转为标准的 \lim\limits_{
  result = result.replace(/\\lim_?\s*(\\limits)?_?\s*\{/g, '\\lim\\limits_{')
  
  // 4. 清除多余的空格
  result = result.replace(/\$\s+/g, '$').replace(/\s+\$/g, '$')

  return result
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const file = input.files[0]
  input.value = ''

  step.value = 'parsing'
  const formData = new FormData()
  formData.append('file', file)

  try {
    // 根据引擎选择不同的接口
    const url = ocrEngine.value === 'llm' ? '/plugins/llm_ocr/parse' : '/plugins/ocr/parse'
    
    const res = await api.post(`${url}?type=${selectedType.value}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000 // 【核心修复】云端 AI 识别需要时间，单独设置 60 秒超时
    })
    
    parsedProblems.value = res.data
    selectedIds.value = res.data.map((p: any) => p.temp_id)
    step.value = 'preview'
  } catch (err: any) {
    console.error('识别失败', err)
    // 【修改】兼容各种奇奇怪怪的报错格式
    let msg = err.message
    if (err.response?.data) {
      if (typeof err.response.data === 'string') {
        msg = err.response.data.substring(0, 100) // 如果是 HTML 报错页，截取前100字
      } else if (err.response.data.detail) {
        msg = err.response.data.detail
      }
    }
    alert('识别失败：' + msg)
    step.value = 'upload' // 即使失败也要退回上传界面
  }
}

async function onImport() {
  importing.value = true
  try {
    const selectedProblems = parsedProblems.value
      .filter(p => selectedIds.value.includes(p.temp_id))
      .map(p => ({
        ...p,
        description: formatLatex(p.description), // 【修复】清洗公式格式
        bank_id: selectedBank.value,   // 注入 bank_id
        paper_id: selectedPaper.value, // 注入 paper_id
        type: selectedType.value,      // 使用用户选择的题型
        category_id: 1,
        difficulty: 1,
        test_cases: [],
        subproblems: []
      }))
      
    // 【修改】调用我们改好的通用批量接口
    const adminKey = localStorage.getItem('admin_key') || ''
    await api.post('/admin/problems/batch', 
      { problems: selectedProblems },
      { headers: { 'X-Admin-Key': adminKey } }
    )
    
    alert('导入成功！')
    emit('success')
    close()
  } catch (err: any) {
    alert('导入失败：' + (err.response?.data?.detail || err.message))
  } finally {
    importing.value = false
  }
}
</script>

<style scoped>
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: white; border-radius: var(--radius-lg); width: 100%; max-width: 600px; display: flex; flex-direction: column; max-height: 90vh; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-md) var(--spacing-lg); border-bottom: 1px solid var(--color-border-light); }
.modal-header h2 { margin: 0; font-size: 16px; }
.modal-close { background: none; border: none; font-size: 24px; cursor: pointer; color: var(--color-text-secondary); }
.modal-body { padding: var(--spacing-lg); overflow-y: auto; flex: 1; }
.modal-footer { padding: var(--spacing-md) var(--spacing-lg); border-top: 1px solid var(--color-border-light); display: flex; justify-content: flex-end; gap: var(--spacing-sm); }
.upload-box { border: 2px dashed var(--color-border); border-radius: var(--radius-md); padding: 60px 20px; text-align: center; cursor: pointer; transition: border-color 0.2s; }
.upload-box:hover { border-color: var(--color-primary); color: var(--color-primary); }
.upload-box p { margin: 0 0 8px; font-size: 16px; font-weight: bold; }
.upload-box small { color: var(--color-text-secondary); }
.loading-area { display: flex; flex-direction: column; align-items: center; padding: 40px; gap: 16px; }
.spinner { width: 40px; height: 40px; border: 4px solid var(--color-border); border-top-color: var(--color-primary); border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.hint { font-size: 13px; color: var(--color-text-secondary); margin-bottom: var(--spacing-md); }
.problem-list { display: flex; flex-direction: column; gap: 12px; }
.problem-item { display: flex; gap: 12px; padding: 12px; background: var(--color-sample-bg); border-radius: var(--radius-md); border: 1px solid var(--color-border-light); cursor: pointer; }
.problem-content { flex: 1; }
.problem-title { font-weight: bold; color: var(--color-text-primary); margin-bottom: 4px; }
.problem-desc { font-size: 12px; color: var(--color-text-secondary); }
.filter-select { padding: 8px 12px; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-bg-page); color: var(--color-text-primary); font-size: 14px; outline: none; }

/* 暗色模式简单适配 */
[data-theme="dark"] .modal { background: var(--color-bg-card); }
[data-theme="dark"] .modal-header h2 { color: var(--color-text-primary); }
[data-theme="dark"] .form-group select { background: var(--color-bg-page); color: var(--color-text-primary); border-color: var(--color-border); }
</style>