<template>
  <div class="code-editor-root" :style="{ height: height }">
    
    <!-- ===== 移动端专属方案：原生输入 + 工具栏 ===== -->
    <div v-if="isMobile" class="mobile-editor-wrapper">
      <textarea
        ref="textareaRef"
        v-model="codeText"
        class="mobile-textarea"
        placeholder="在此输入代码..."
        spellcheck="false"
        @input="onMobileInput"
      ></textarea>
      
      <!-- 移动端快捷符号工具栏 (沉浸式) -->
      <div class="mobile-toolbar">
        <button @click="insertText('\t')">Tab</button>
        <button @click="insertText('{')">{</button>
        <button @click="insertText('}')">}</button>
        <button @click="insertText('(')">(</button>
        <button @click="insertText(')')">)</button>
        <button @click="insertText('[')">[</button>
        <button @click="insertText(']')">]</button>
        <button @click="insertText(';')">;</button>
        <button @click="insertText('\'')">'</button>
        <button @click="insertText('&quot;')">"</button>
        <button @click="insertText(':')">:</button>
        <button @click="insertText('\n')">↵</button>
      </div>
    </div>

    <!-- ===== 桌面端方案：Monaco Editor ===== -->
    <div v-else ref="editorContainer" class="monaco-container"></div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api'
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'

self.MonacoEnvironment = {
  getWorker() {
    return new EditorWorker()
  },
}

const props = defineProps<{
  modelValue: string
  language: string
  height?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const isMobile = computed(() => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
})

// ===== 移动端逻辑 =====
const codeText = ref(props.modelValue)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function onMobileInput() {
  emit('update:modelValue', codeText.value)
}

// 插入符号并处理 Tab 缩进
function insertText(text: string) {
  const el = textareaRef.value
  if (!el) return

  const start = el.selectionStart
  const end = el.selectionEnd
  const val = el.value

  if (text === '\t') {
    // 插入 4 个空格代替 Tab
    el.value = val.substring(0, start) + '    ' + val.substring(end)
    el.selectionStart = el.selectionEnd = start + 4
  } else {
    el.value = val.substring(0, start) + text + val.substring(end)
    el.selectionStart = el.selectionEnd = start + text.length
  }

  codeText.value = el.value
  emit('update:modelValue', el.value)
  
  nextTick(() => {
    el.focus()
  })
}

// ===== 桌面端 Monaco 逻辑 =====
const editorContainer = ref<HTMLElement | null>(null)
let editorInstance: monaco.editor.IStandaloneCodeEditor | null = null
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (isMobile.value || !editorContainer.value) return

  editorInstance = monaco.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language,
    theme: 'vs',
    automaticLayout: false,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 14,
    lineHeight: 1.6,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    occurrencesHighlight: 'off',
    codeLens: false,
    hover: { enabled: true },
    quickSuggestions: true,
    matchBrackets: 'never',
    folding: false,
    renderLineHighlight: 'none',
    guides: { indentation: false },
  })

  editorInstance.onDidChangeModelContent(() => {
    const val = editorInstance!.getValue()
    if (val !== props.modelValue) {
      emit('update:modelValue', val)
    }
  })

  resizeObserver = new ResizeObserver(() => {
    editorInstance?.layout()
  })
  resizeObserver.observe(editorContainer.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (editorInstance) {
    editorInstance.dispose()
    editorInstance = null
  }
})

watch(() => props.modelValue, (newVal) => {
  if (isMobile.value) {
    if (newVal !== codeText.value) {
      codeText.value = newVal
    }
  } else {
    if (editorInstance && newVal !== editorInstance.getValue()) {
      editorInstance.setValue(newVal)
    }
  }
})

watch(() => props.language, (newLang) => {
  if (!isMobile.value && editorInstance) {
    const model = editorInstance.getModel()
    if (model) monaco.editor.setModelLanguage(model, newLang)
  }
})
</script>

<style scoped>
.code-editor-root {
  width: 100%;
  overflow: hidden;
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  display: flex;
  flex-direction: column;
}

.monaco-container {
  width: 100%;
  height: 100%;
}

/* 移动端编辑器容器 */
.mobile-editor-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: #f9fafb;
}

/* 移动端输入框 */
.mobile-textarea {
  flex: 1;
  width: 100%;
  padding: 12px;
  border: none;
  resize: none;
  outline: none;
  background: transparent;
  color: #1d1d1f;
  font-family: 'Consolas', 'Monaco', monospace;
  /* 针对 1440P 高分辨率屏幕，字号适当调大 */
  font-size: 15px;
  line-height: 1.6;
  box-sizing: border-box;
  white-space: pre;
  overflow-x: auto;
}

/* 移动端快捷符号工具栏 */
.mobile-toolbar {
  display: flex;
  gap: 8px;
  padding: 10px;
  background: #e5e7eb;
  border-top: 1px solid #d1d5db;
  overflow-x: auto;
  scrollbar-width: none;
  /* 防止被键盘挤压 */
  flex-shrink: 0;
}

.mobile-toolbar::-webkit-scrollbar {
  display: none;
}

.mobile-toolbar button {
  padding: 8px 14px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-family: monospace;
  font-size: 16px;
  color: #374151;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.mobile-toolbar button:active {
  background: #e5e7eb;
  transform: translateY(1px);
}
</style>