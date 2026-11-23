<template>
  <div :class="['empty-state', variant]">
    <div class="es-icon" aria-hidden="true" v-html="iconSvg"></div>
    <h2 class="es-title">{{ title }}</h2>
    <p class="es-desc">{{ description }}</p>

    <div v-if="detail" class="es-detail">{{ detail }}</div>

    <div class="es-actions">
      <button v-if="retryLabel" class="btn-primary" :disabled="retrying" @click="$emit('retry')">
        {{ retrying ? '检测中…' : retryLabel }}
      </button>
      <slot name="actions"></slot>
    </div>

    <p v-if="hint" class="es-hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  variant?: 'offline' | 'empty' | 'error'
  title: string
  description?: string
  detail?: string
  hint?: string
  retryLabel?: string
  retrying?: boolean
}>(), {
  variant: 'empty',
  description: '',
  detail: '',
  hint: '',
  retryLabel: '',
  retrying: false
})

defineEmits<{ (e: 'retry'): void }>()

const icons = {
  offline: `<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 8.5a16 16 0 0 1 20 0"/><path d="M5 12.5a11 11 0 0 1 14 0"/><path d="M8.5 16.5a6 6 0 0 1 7 0"/><path d="M12 20h.01"/><path d="M3 3l18 18"/></svg>`,
  empty: `<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7h18"/><path d="M5 7v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7"/><path d="M9 11h6"/></svg>`,
  error: `<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5"/><path d="M12 16h.01"/></svg>`
}

const iconSvg = computed(() => icons[props.variant] || icons.empty)
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 20px;
  margin: 0 auto;
  max-width: 520px;
  text-align: center;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.es-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  margin-bottom: 14px;
  border-radius: 50%;
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.empty-state.offline .es-icon {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.empty-state.error .es-icon {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.es-title {
  margin: 0 0 6px;
  font-size: var(--font-size-subtitle);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.es-desc {
  margin: 0;
  font-size: var(--font-size-body);
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.es-detail {
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-sample-bg);
  color: var(--color-text-muted);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-small);
  word-break: break-all;
}

.es-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 18px;
}

.es-actions:empty {
  display: none;
}

.es-hint {
  margin: 14px 0 0;
  font-size: var(--font-size-small);
  line-height: 1.6;
  color: var(--color-text-muted);
}

@media (max-width: 640px) {
  .empty-state {
    padding: 36px 16px;
    border-radius: var(--radius-md);
  }
}
</style>