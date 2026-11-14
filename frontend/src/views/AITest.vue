<template>
  <div class="ai-test-page">
    <h1>AI 流式对话测试</h1>
    <div class="chat-box">
      <div v-for="(msg, idx) in messages" :key="idx" :class="['message', msg.role]">
        <strong>{{ msg.role === 'user' ? '我' : 'AI' }}:</strong>
        <span style="white-space: pre-wrap;">{{ msg.content }}</span>
      </div>
    </div>
    <div class="input-area">
      <input v-model="input" @keyup.enter="send" placeholder="输入消息..." />
      <button @click="send" :disabled="loading">发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { streamChat, type ChatMessage } from '../api/ai'

const messages = ref<ChatMessage[]>([])
const input = ref('')
const loading = ref(false)

async function send() {
  if (!input.value.trim() || loading.value) return
  
  const userMsg = input.value.trim()
  input.value = ''
  
  messages.value.push({ role: 'user', content: userMsg })
  
  const aiMsg: ChatMessage = { role: 'assistant', content: '' }
  messages.value.push(aiMsg)
  const aiIndex = messages.value.length - 1
  
  loading.value = true

  await streamChat(
    messages.value.slice(0, -1), // 不把空的 AI 回复传过去
    (text) => {
      messages.value[aiIndex].content += text
    },
    (err) => {
      messages.value[aiIndex].content += `\n[错误]: ${err.message}`
      loading.value = false
    },
    () => {
      loading.value = false
    }
  )
}
</script>

<style scoped>
.ai-test-page {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}
.chat-box {
  border: 1px solid var(--color-border);
  height: 400px;
  overflow-y: auto;
  padding: 16px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: var(--color-bg-card);
}
.message {
  margin-bottom: 12px;
  line-height: 1.5;
}
.message.user { color: var(--color-primary); }
.input-area {
  display: flex;
  gap: 12px;
}
.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}
.input-area button {
  padding: 10px 24px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>