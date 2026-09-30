<template>
  <div ref="containerRef" class="code-editor-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

// 只加载编辑器核心 API，不加载全部语言
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api'

// 只加载需要的三种语言
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution'
import 'monaco-editor/esm/vs/basic-languages/java/java.contribution'
import 'monaco-editor/esm/vs/basic-languages/cpp/cpp.contribution'

import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'

self.MonacoEnvironment = {
  getWorker() {
    return new EditorWorker()
  },
}

const props = withDefaults(
  defineProps<{
    modelValue: string
    language?: string
    height?: string
    readonly?: boolean
  }>(),
  {
    language: 'python',
    height: '360px',
    readonly: false,
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const containerRef = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null
let resizeObserver: ResizeObserver | null = null

function normalizeLanguage(lang: string): string {
  const map: Record<string, string> = {
    python: 'python',
    java: 'java',
    cpp: 'cpp',
    'c++': 'cpp',
  }
  return map[lang] || 'plaintext'
}

onMounted(() => {
  if (!containerRef.value) return

  // 用 IntersectionObserver 等容器进入视口再初始化
  const initObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      initObserver.disconnect()
      createEditor()
    }
  }, { rootMargin: '200px' })

  initObserver.observe(containerRef.value)

  function createEditor() {
    if (!containerRef.value) return

    editor = monaco.editor.create(containerRef.value, {
      value: props.modelValue,
      language: normalizeLanguage(props.language),
      theme: 'vs',
      fontSize: 13,
      fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
      lineNumbers: 'on',
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      automaticLayout: false,
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'on',
      readOnly: props.readonly,

      // ===== 性能优化 =====
      renderWhitespace: 'none',
      renderLineHighlight: 'none',
      occurrencesHighlight: 'off',
      selectionHighlight: false,
      codeLens: false,
      folding: false,
      glyphMargin: false,
      lineDecorationsWidth: 8,
      lineNumbersMinChars: 3,
      quickSuggestions: false,
      suggestOnTriggerCharacters: false,
      wordBasedSuggestions: 'off',
      parameterHints: { enabled: false },
      hover: { enabled: false },
      contextmenu: false,
      matchBrackets: 'never',
      guides: { indentation: false },
      smoothScrolling: false,
      cursorBlinking: 'blink',
      padding: { top: 12, bottom: 12 },
      scrollbar: {
        verticalScrollbarSize: 8,
        horizontalScrollbarSize: 8,
        useShadows: false,
      },
    })

    editor.onDidChangeModelContent(() => {
      emit('update:modelValue', editor!.getValue())
    })

    resizeObserver = new ResizeObserver(() => {
      editor?.layout()
    })
    resizeObserver.observe(containerRef.value)
  }
})

onBeforeUnmount(() => {
  if (resizeObserver && containerRef.value) {
    resizeObserver.unobserve(containerRef.value)
  }
  resizeObserver = null

  if (editor) {
    editor.dispose()
    editor = null
  }
})

// 外部 v-model 变化 → 更新编辑器
watch(
  () => props.modelValue,
  (newVal) => {
    if (!editor) return
    if (editor.getValue() !== newVal) {
      editor.setValue(newVal || '')
    }
  }
)

// 语言切换
watch(
  () => props.language,
  (newLang) => {
    if (!editor) return
    const model = editor.getModel()
    if (model) {
      monaco.editor.setModelLanguage(model, normalizeLanguage(newLang))
    }
  }
)
</script>

<style scoped>
.code-editor-container {
  width: 100%;
  height: v-bind(height);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #fff;
}

.code-editor-container:focus-within {
  border-color: var(--color-primary);
}
</style>