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

      <div class="mobile-toolbar">
        <button type="button" @click="insertText('\t')">Tab</button>
        <button type="button" @click="insertText('{')">{</button>
        <button type="button" @click="insertText('}')">}</button>
        <button type="button" @click="insertText('(')">(</button>
        <button type="button" @click="insertText(')')">)</button>
        <button type="button" @click="insertText('[')">[</button>
        <button type="button" @click="insertText(']')">]</button>
        <button type="button" @click="insertText(';')">;</button>
        <button type="button" @click="insertText('\'')">'</button>
        <button type="button" @click="insertText('&quot;')">"</button>
        <button type="button" @click="insertText(':')">:</button>
        <button type="button" @click="insertText('\n')">↵</button>
      </div>
    </div>

    <!-- ===== 桌面端方案：Monaco Editor（懒加载） ===== -->
    <div v-else ref="editorContainer" class="monaco-container"></div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed, nextTick } from 'vue'
// 只引入类型，不会打包 Monaco 到 JS
import type * as Monaco from 'monaco-editor/esm/vs/editor/editor.api'

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

function getCurrentTheme(): string {
  return document.documentElement.hasAttribute('data-theme') ? 'vs-dark' : 'vs'
}

// ===== 移动端逻辑 =====
const codeText = ref(props.modelValue)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function onMobileInput() {
  emit('update:modelValue', codeText.value)
}

function insertText(text: string) {
  const el = textareaRef.value
  if (!el) return

  const start = el.selectionStart
  const end = el.selectionEnd
  const val = el.value

  if (text === '\t') {
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

// ===== 桌面端 Monaco 逻辑（懒加载） =====
const editorContainer = ref<HTMLElement | null>(null)
let monacoApi: typeof Monaco | null = null
let editorInstance: Monaco.editor.IStandaloneCodeEditor | null = null
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null

onMounted(async () => {
  if (isMobile.value || !editorContainer.value) return

  // 动态加载 Monaco 与 Worker，移动端不会触发这段代码
  const monacoModule = await import('monaco-editor/esm/vs/editor/editor.api')
  const EditorWorkerCtor = (await import('monaco-editor/esm/vs/editor/editor.worker?worker')).default as new () => Worker
  monacoApi = monacoModule

  self.MonacoEnvironment = {
    getWorker() {
      return new EditorWorkerCtor()
    },
  }

  // 组件可能在 await 期间被卸载
  if (!editorContainer.value) return

  editorInstance = monacoModule.editor.create(editorContainer.value, {
    value: props.modelValue,
    language: props.language,
    theme: getCurrentTheme(),
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
    padding: { top: 12, bottom: 12 },
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

  // 监听暗色模式切换
  themeObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'data-theme' && monacoApi) {
        monacoApi.editor.setTheme(getCurrentTheme())
      }
    })
  })
  themeObserver.observe(document.documentElement, { attributes: true })
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (themeObserver) themeObserver.disconnect()
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
  if (!isMobile.value && editorInstance && monacoApi) {
    const model = editorInstance.getModel()
    if (model) monacoApi.editor.setModelLanguage(model, newLang)
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
  border: 1px solid var(--color-border);
}

.monaco-container {
  width: 100%;
  height: 100%;
  background: var(--color-bg-card);
}

/* 移动端编辑器容器 */
.mobile-editor-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: var(--color-sample-bg);
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
  color: var(--color-text-primary);
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 15px;
  line-height: 1.6;
  box-sizing: border-box;
  white-space: pre;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* 移动端快捷符号工具栏 */
.mobile-toolbar {
  display: flex;
  gap: 8px;
  padding: 10px;
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
  overflow-x: auto;
  scrollbar-width: none;
  flex-shrink: 0;
  -webkit-overflow-scrolling: touch;
}

.mobile-toolbar::-webkit-scrollbar {
  display: none;
}

.mobile-toolbar button {
  padding: 8px 14px;
  background: var(--color-bg-page);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-family: monospace;
  font-size: 16px;
  color: var(--color-text-primary);
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.mobile-toolbar button:active {
  background: var(--color-primary-light);
  transform: translateY(1px);
}
</style>