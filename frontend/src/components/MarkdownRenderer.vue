<template>
  <div class="markdown-body" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from '../utils/marked'

const props = defineProps<{ content: string }>()

const rendered = computed(() => {
  if (!props.content) return ''
  return marked(props.content)
})
</script>

<style scoped>
.markdown-body {
  line-height: 1.6;
}

.markdown-body :deep(pre) {
  background: #f6f8fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-body :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  background: #f0f0f0;
  padding: 2px 4px;
  border-radius: 3px;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  display: block;
}

.markdown-body :deep(pre code.hljs) {
  background: transparent;
  padding: 0;
}

.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-body :deep(p) {
  margin: 8px 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 24px;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #d1d5db;
  padding-left: 12px;
  color: #6b7280;
  margin: 8px 0;
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 6px 12px;
}

.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
</style>