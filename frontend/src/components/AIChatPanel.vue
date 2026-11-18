<template>
  <div class="ai-panel" :style="panelStyle">
    <div v-if="!isMobile" class="resize-handle-top-left" @mousedown="startResize"></div>
    <div class="ai-header">
      <span>AI 助教</span>
      <button @click="$emit('close')">×</button>
    </div>
    <div class="ai-messages" ref="msgContainer">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['msg', msg.role]">
        <MarkdownRenderer 
          v-if="msg.role === 'assistant'" 
          :content="msg.content" 
          :streaming="loading && idx === messages.length - 1" 
        />
        <div v-else>{{ msg.content }}</div>
      </div>
    </div>
    <div class="ai-input">
      <textarea v-model="input" placeholder="遇到难题了？问我试试..." @keyup.enter.prevent="send"></textarea>
      <button @click="send" :disabled="loading">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted, computed } from 'vue'
import { streamChat, type ChatMessage } from '../api/ai'
import MarkdownRenderer from './MarkdownRenderer.vue'

const emit = defineEmits(['close'])
const messages = ref<ChatMessage[]>([{ role: 'assistant', content: '你好！我是你的 AI 助教，有什么可以帮你的吗？' }])
const input = ref('')
const loading = ref(false)
const msgContainer = ref<HTMLElement | null>(null)

// 【核心修复】移动端适配
const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
const panelWidth = ref(isMobile ? window.innerWidth : 450)
const panelHeight = ref(isMobile ? window.innerHeight : 650)

const panelStyle = computed(() => {
  if (isMobile) {
    return { width: '100vw', height: '100vh', right: '0', bottom: '0', borderRadius: '0', border: 'none' }
  }
  return { width: panelWidth.value + 'px', height: panelHeight.value + 'px' }
})

// ===== 拖拽逻辑 =====
let isResizing = false, startX = 0, startY = 0, startWidth = 0, startHeight = 0
function startResize(e: MouseEvent) {
  isResizing = true; startX = e.clientX; startY = e.clientY
  startWidth = panelWidth.value; startHeight = panelHeight.value
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopResize)
  e.preventDefault()
}
function onMouseMove(e: MouseEvent) {
  if (!isResizing) return
  panelWidth.value = Math.max(320, Math.min(startWidth + (startX - e.clientX), window.innerWidth - 40))
  panelHeight.value = Math.max(400, Math.min(startHeight + (startY - e.clientY), window.innerHeight - 40))
}
function stopResize() {
  isResizing = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopResize)
}
onUnmounted(() => stopResize())

// ===== 核心聊天逻辑 =====
async function doSend(text: string) {
  if (!text.trim() || loading.value) return
  
  messages.value.push({ role: 'user', content: text })
  const aiMsg = { role: 'assistant' as const, content: '' }
  messages.value.push(aiMsg)
  const idx = messages.value.length - 1
  
  loading.value = true
  scrollToBottom()

  await streamChat(
    messages.value.slice(0, -1),
    (chunk) => {
      if (chunk.includes('[DONE]')) return
      messages.value[idx].content += chunk
      scrollToBottom()
    },
    (err) => { messages.value[idx].content += `\n\n[错误: ${err.message}]`; loading.value = false },
    () => { loading.value = false }
  )
}

function send() {
  const text = input.value
  input.value = ''
  doSend(text)
}

function scrollToBottom() {
  nextTick(() => { if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight })
}

defineExpose({ triggerQuery(text: string) { doSend(text) } })
</script>

<style scoped>
.ai-panel { position: fixed; right: 20px; bottom: 20px; background: var(--color-bg-card); border: 1px solid var(--color-border); border-radius: 12px; box-shadow: var(--shadow-card-hover); display: flex; flex-direction: column; z-index: 1000; resize: none; }
.resize-handle-top-left { position: absolute; top: 0; left: 0; width: 24px; height: 24px; cursor: nwse-resize; z-index: 10; }
.resize-handle-top-left::before { content: ''; position: absolute; top: 6px; left: 6px; width: 0; height: 0; border-top: 4px solid var(--color-border); border-left: 4px solid var(--color-border); }
.ai-header { padding: 12px 16px; border-bottom: 1px solid var(--color-border-light); display: flex; justify-content: space-between; font-weight: bold; flex-shrink: 0; }
.ai-header button { background: none; border: none; font-size: 24px; cursor: pointer; color: var(--color-text-secondary); }
.ai-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.msg { padding: 10px 14px; border-radius: 8px; max-width: 95%; line-height: 1.5; }
.msg.assistant { background: var(--color-sample-bg); align-self: flex-start; width: 100%; }
.msg.user { background: var(--color-primary); color: white; align-self: flex-end; }
.ai-input { padding: 12px; border-top: 1px solid var(--color-border-light); display: flex; gap: 8px; flex-shrink: 0; padding-bottom: max(12px, env(safe-area-inset-bottom)); }
.ai-input textarea { flex: 1; resize: none; height: 40px; border: 1px solid var(--color-border); border-radius: 6px; padding: 10px; background: var(--color-bg-page); color: var(--color-text-primary); font-family: inherit; }
.ai-input button { padding: 0 16px; background: var(--color-primary); color: white; border: none; border-radius: 6px; cursor: pointer; }
</style>