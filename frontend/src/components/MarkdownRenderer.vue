<template>
  <div class="markdown-body" ref="containerRef" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { marked } from '../utils/marked'
import { getBackendUrl } from '../utils/backend-url'

// 使用标准的 props 定义，避免 TS 报错
const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  streaming: {
    type: Boolean,
    default: false
  }
})

const containerRef = ref<HTMLElement | null>(null)

function sanitizeMath(text: string): string {
  if (!text) return text
  return text.replace(/\$\$([\s\S]*?)\$\$/g, (match: string, formula: string) => {
    const left = (formula.match(/\{/g) || []).length
    const right = (formula.match(/\}/g) || []).length
    if (left !== right) {
      return formula.replace(/[\$\{\}]/g, '')
    }
    return match
  })
}

const rendered = computed(() => {
  if (!props.content) return ''
  let content = String(props.content)
  
  const base = getBackendUrl()
  content = content.replace(/\/api\/image\//g, '/api/images/')
  if (base) {
    content = content.replace(/!\[([^\]]*)\]\(\/api\//g, `![$1](${base}/api/`)
  }

  content = sanitizeMath(content)

  // 保护 $$ 和 \[
  const blockMaths: string[] = []
  content = content.replace(/(\$\$|\\\[)([\s\S]*?)(\$\$|\\\])/g, (match: string) => {
    const id = `@@BLOCK_MATH_${blockMaths.length}@@`
    blockMaths.push(match)
    return id
  })
  
  // 保护 $ 和 \(
  const inlineMaths: string[] = []
  content = content.replace(/(\$|\\\()([^\$\n]+?)(\$|\\\))/g, (match: string) => {
    const id = `@@INLINE_MATH_${inlineMaths.length}@@`
    inlineMaths.push(match)
    return id
  })

  let html = marked(content) as string

  html = html.replace(/@@BLOCK_MATH_(\d+)@@/g, (_match: string, idx: string) => blockMaths[Number(idx)])
  html = html.replace(/@@INLINE_MATH_(\d+)@@/g, (_match: string, idx: string) => inlineMaths[Number(idx)])

  return html
})

watch(rendered, () => {
  if (props.streaming) return // 流式输出中不渲染 MathJax

  nextTick(() => {
    if ((window as any).MathJax && containerRef.value) {
      (window as any).MathJax.typesetPromise([containerRef.value]).catch((err: any) => {
        console.warn('MathJax 渲染警告', err)
      })
    }
  })
}, { immediate: true })

watch(() => props.streaming, (isStreaming) => {
  if (!isStreaming) {
    nextTick(() => {
      if ((window as any).MathJax && containerRef.value) {
        (window as any).MathJax.typesetPromise([containerRef.value]).catch((err: any) => {
          console.warn('MathJax 渲染警告', err)
        })
      }
    })
  }
})
</script>

<style scoped>
.markdown-body { line-height: 1.6; color: var(--color-text-primary); }
.markdown-body :deep(pre) { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; border: 1px solid var(--color-border-light); }
.markdown-body :deep(code) { font-family: 'Consolas', 'Monaco', monospace; background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-size: 13px; }
.markdown-body :deep(pre code) { background: transparent; padding: 0; display: block; }
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 16px; margin-bottom: 8px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(table) { border-collapse: collapse; margin: 8px 0; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #e5e7eb; padding: 6px 12px; }

/* 暗色模式 */
[data-theme="dark"] .markdown-body :deep(pre) { background: #000000; border: 1px solid #333333; color: #d4d4d4; }
[data-theme="dark"] .markdown-body :deep(code) { background: #1e1e1e; color: #d4d4d4; }
[data-theme="dark"] .markdown-body :deep(pre code) { background: transparent; }
[data-theme="dark"] .markdown-body :deep(th), [data-theme="dark"] .markdown-body :deep(td) { border-color: var(--color-border); }

/* 隐藏 MathJax 渲染错误的红字 */
mjx-merror, .MathJax_Error {
  display: none !important;
}
</style>