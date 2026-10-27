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
          <input
            type="file"
            accept="image/*"
            capture="environment"
            style="display: none"
            ref="fileInputRef"
            @change="onFileSelected"
          />
          <div class="upload-box" @click="fileInputRef?.click()">
            <p>点击此处拍照或选择图片</p>
            <small>支持一图多题，AI 将自动切分</small>
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
          <div class="problem-list">
            <label v-for="(p, idx) in parsedProblems" :key="p.temp_id" class="problem-item">
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
        <button 
          v-if="step === 'preview'" 
          class="btn-primary" 
          :disabled="selectedIds.length === 0 || importing"
          @click="onImport"
        >
          {{ importing ? '导入中...' : `导入选中的 ${selectedIds.length} 道题` }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '../utils/axios'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits(['close', 'success'])

const step = ref<'upload' | 'parsing' | 'preview'>('upload')
const fileInputRef = ref<HTMLInputElement | null>(null)
const parsedProblems = ref<any[]>([])
const selectedIds = ref<string[]>([])
const importing = ref(false)

function close() {
  if (step.value === 'parsing') return // 识别中不允许关闭
  step.value = 'upload'
  parsedProblems.value = []
  selectedIds.value = []
  emit('close')
}

async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  const file = input.files[0]
  input.value = '' // 允许重复选同一张图

  step.value = 'parsing'
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await api.post('/plugins/ocr/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    parsedProblems.value = res.data
    selectedIds.value = res.data.map((p: any) => p.temp_id) // 默认全选
    step.value = 'preview'
  } catch (err: any) {
    alert('识别失败：' + (err.response?.data?.detail || err.message))
    step.value = 'upload'
  }
}

async function onImport() {
  importing.value = true
  try {
    const selectedProblems = parsedProblems.value.filter(p => selectedIds.value.includes(p.temp_id))
    await api.post('/plugins/ocr/batch-import', { problems: selectedProblems })
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
/* 直接复用系统已有的 modal 样式规范 */
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
</style>