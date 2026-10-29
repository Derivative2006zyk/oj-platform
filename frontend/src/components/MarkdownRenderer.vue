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
  return text.replace(/\$\$([\s\S]*?)\$\$/g, (match, formula) => {
    const left = (formula.match(/\{/g) || []).length
    const right = (formula.match(/\}/g) || []).length
    if (left !== right) {
      // 不匹配，去掉了 $、{ 和 }，防止报错
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
  content = content.replace(/\$\$([\s\S]*?)\$\$/g, (match) => {
    const id = `@@BLOCK_MATH_${mathBlocks.length}@@`
    mathBlocks.push(match)
    return id
  })
  
  const mathInlines: string[] = []
  content = content.replace(/\$([^\$\n]+?)\$/g, (match) => {
    const id = `@@INLINE_MATH_${mathInlines.length}@@`
    mathInlines.push(match)
    return id
  })

  // 4. marked 解析
  let html = marked(content)

  // 5. 替换回原公式（此时它们已经安全地呆在 HTML 中）
  html = html.replace(/@@BLOCK_MATH_(\d+)@@/g, (_, idx) => mathBlocks[Number(idx)])
  html = html.replace(/@@INLINE_MATH_(\d+)@@/g, (_, idx) => mathInlines[Number(idx)])

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
.markdown-body { line-height: 1.6; }
.markdown-body :deep(pre) { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
.markdown-body :deep(code) { font-family: 'Consolas', 'Monaco', monospace; background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
.markdown-body :deep(pre code) { background: transparent; padding: 0; display: block; }
.markdown-body :deep(img) { max-width: 100%; border-radius: 8px; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 16px; margin-bottom: 8px; }
.markdown-body :deep(p) { margin: 8px 0; }
.markdown-body :deep(table) { border-collapse: collapse; margin: 8px 0; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid #e5e7eb; padding: 6px 12px; }
</style>