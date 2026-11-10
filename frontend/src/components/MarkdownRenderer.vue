<template>
  <div class="markdown-body" ref="containerRef" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { marked } from '../utils/marked'
import { getBackendUrl } from '../utils/backend-url'

const props = defineProps<{ content: string }>()
const containerRef = ref<HTMLElement | null>(null)

// 暴力清洗公式，过滤掉括号不匹配的垃圾公式
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
  
  // 1. 替换图片相对路径
  const base = getBackendUrl()
  content = content.replace(/\/api\/image\//g, '/api/images/')
  if (base) {
    content = content.replace(/!\[([^\]]*)\]\(\/api\//g, `![$1](${base}/api/`)
  }

  // 2. 清洗错误的公式
  content = sanitizeMath(content)

  // 3. 核心：把 $$ 和 $ 保护起来，不让 marked 破坏它们
  const mathBlocks: string[] = []
  content = content.replace(/\$\$([\s\S]*?)\$\$/g, (match: string) => {
    const id = `@@BLOCK_MATH_${mathBlocks.length}@@`
    mathBlocks.push(match)
    return id
  })
  
  const mathInlines: string[] = []
  content = content.replace(/\$([^\$\n]+?)\$/g, (match: string) => {
    const id = `@@INLINE_MATH_${mathInlines.length}@@`
    mathInlines.push(match)
    return id
  })

  // 4. marked 解析 (强制断言为 string)
  let html = marked(content) as string

  // 5. 替换回原公式（显式标注参数类型）
  html = html.replace(/@@BLOCK_MATH_(\d+)@@/g, (_match: string, idx: string) => mathBlocks[Number(idx)])
  html = html.replace(/@@INLINE_MATH_(\d+)@@/g, (_match: string, idx: string) => mathInlines[Number(idx)])

  return html
})

// 6. 每次 DOM 更新后，触发 MathJax 渲染
watch(rendered, () => {
  nextTick(() => {
    if ((window as any).MathJax && containerRef.value) {
      (window as any).MathJax.typesetPromise([containerRef.value]).catch((err: any) => {
        console.warn('MathJax 渲染警告', err)
      })
    }
  })
}, { immediate: true })
</script>

<style scoped>
.markdown-body { 
  line-height: 1.6; 
  color: var(--color-text-primary);
}

/* 代码块在亮色模式下的默认样式 */
.markdown-body :deep(pre) { 
  background: #f6f8fa; 
  padding: 12px; 
  border-radius: 6px; 
  overflow-x: auto; 
  border: 1px solid var(--color-border-light);
}
.markdown-body :deep(code) { 
  font-family: 'Consolas', 'Monaco', monospace; 
  background: #f0f0f0; 
  padding: 2px 4px; 
  border-radius: 3px; 
  font-size: 13px;
}
.markdown-body :deep(pre code) { 
  background: transparent; 
  padding: 0; 
  display: block; 
}
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 16px; margin-bottom: 8px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(table) { border-collapse: collapse; margin: 8px 0; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #e5e7eb; padding: 6px 12px; }

/* ===== 暗色模式专属覆盖 ===== */
[data-theme="dark"] .markdown-body :deep(pre) {
  background: #000000;      /* 纯黑代码块背景 */
  border: 1px solid #333333;
  color: #d4d4d4;
}
[data-theme="dark"] .markdown-body :deep(code) {
  background: #1e1e1e;
  color: #d4d4d4;
}
[data-theme="dark"] .markdown-body :deep(pre code) {
  background: transparent;
}
[data-theme="dark"] .markdown-body :deep(th), 
[data-theme="dark"] .markdown-body :deep(td) {
  border-color: var(--color-border);
}
</style>