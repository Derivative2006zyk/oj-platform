<template>
  <div v-if="visible" class="conflict-mask" @click.self="$emit('close')">
    <div class="conflict-dialog">
      <header class="cd-header">
        <h2>保存冲突</h2>
        <button class="cd-close" @click="$emit('close')">×</button>
      </header>

      <div class="cd-body">
        <p class="cd-summary">
          题目 #{{ conflict?.problem_id }} 已被其他设备修改
          （你的版本 {{ conflict?.client_version }}，服务器版本 {{ conflict?.server_version }}）。
        </p>

        <p v-if="mergeable" class="cd-ok">
          双方修改了不同的字段，可自动合并。
        </p>
        <p v-else class="cd-warn">
          以下字段双方都改过：{{ overlapLabels }}
        </p>

        <details v-if="!mergeable" class="cd-compare" open>
          <summary>逐字段对比</summary>
          <div v-for="field in conflictFields" :key="field" class="cd-row">
            <div class="cd-field">{{ labelOf(field) }}</div>
            <div class="cd-values">
              <label class="cd-choice">
                <input
                  type="radio"
                  :name="`resolve-${field}`"
                  :value="'local'"
                  v-model="choices[field]"
                />
                本地：{{ preview(local[field]) }}
              </label>
              <label class="cd-choice">
                <input
                  type="radio"
                  :name="`resolve-${field}`"
                  :value="'server'"
                  v-model="choices[field]"
                />
                服务器：{{ preview(server[field]) }}
              </label>
            </div>
          </div>
        </details>
      </div>

      <footer class="cd-footer">
        <button class="btn-ghost" @click="$emit('resolve', { mode: 'server' })">保留服务器</button>
        <button v-if="mergeable" class="btn-primary" @click="$emit('resolve', { mode: 'merge' })">自动合并</button>
        <button v-else class="btn-primary" @click="onManual">按选择合并</button>
        <button class="btn-ghost danger" @click="$emit('resolve', { mode: 'local' })">保留本地并重试</button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { FIELD_LABELS, MERGEABLE_FIELDS, isEqual, type ConflictDetail } from '../utils/merge'

const props = defineProps<{
  visible: boolean
  conflict: ConflictDetail | null
  local: Record<string, any>
  base: Record<string, any> | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'resolve', payload: { mode: 'local' | 'server' | 'merge' | 'manual'; fields?: Record<string, 'local' | 'server'> }): void
}>()

const server = computed(() => props.conflict?.server ?? {})

const localChanged = computed(() =>
  MERGEABLE_FIELDS.filter((f) => !isEqual(props.local[f], props.base?.[f]))
)
const serverChanged = computed(() =>
  MERGEABLE_FIELDS.filter((f) => !isEqual(server.value[f], props.base?.[f]))
)
const overlap = computed(() => localChanged.value.filter((f) => serverChanged.value.includes(f)))
const mergeable = computed(() => !!props.base && overlap.value.length === 0)

const conflictFields = computed(() =>
  MERGEABLE_FIELDS.filter((f) => !isEqual(props.local[f], server.value[f]))
)

const overlapLabels = computed(() => overlap.value.map(labelOf).join('、'))

const choices = reactive<Record<string, 'local' | 'server'>>({})

watch(
  () => props.visible,
  (v) => {
    if (!v) return
    Object.keys(choices).forEach((k) => delete choices[k])
    conflictFields.value.forEach((f) => {
      choices[f] = serverChanged.value.includes(f) ? 'server' : 'local'
    })
  },
  { immediate: true }
)

function labelOf(field: string) {
  return FIELD_LABELS[field] || field
}

function preview(value: any) {
  const text = typeof value === 'string' ? value : JSON.stringify(value ?? '')
  const flat = (text || '').replace(/\s+/g, ' ')
  return flat.length > 60 ? flat.slice(0, 60) + '…' : flat || '（空）'
}

function onManual() {
  emit('resolve', { mode: 'manual', fields: { ...choices } })
}
</script>

<style scoped>
.conflict-mask {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: rgba(0, 0, 0, 0.45);
}

.conflict-dialog {
  width: 100%;
  max-width: 720px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.cd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.cd-header h2 { margin: 0; font-size: 16px; }

.cd-close {
  width: 28px; height: 28px;
  border: none; border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 20px; line-height: 1;
  cursor: pointer;
}

.cd-close:hover { background: var(--color-primary-light); }

.cd-body { padding: var(--spacing-lg); overflow-y: auto; }
.cd-summary { margin: 0 0 10px; font-size: 14px; color: var(--color-text-primary); }
.cd-ok { margin: 0 0 12px; padding: 8px 12px; border-radius: var(--radius-sm); background: var(--color-success-bg); color: var(--color-success-text); font-size: 13px; }
.cd-warn { margin: 0 0 12px; padding: 8px 12px; border-radius: var(--radius-sm); background: var(--color-warning-bg); color: var(--color-warning-text); font-size: 13px; }

.cd-compare { margin-top: 8px; }
.cd-compare summary { cursor: pointer; font-size: 13px; color: var(--color-text-secondary); }

.cd-row {
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.cd-field { font-weight: 600; font-size: 13px; margin-bottom: 6px; }
.cd-values { display: flex; flex-direction: column; gap: 6px; }
.cd-choice { display: flex; gap: 8px; font-size: 13px; color: var(--color-text-secondary); cursor: pointer; }

.cd-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.btn-primary, .btn-ghost {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-primary);
}

.btn-primary { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.btn-ghost.danger { color: var(--color-danger-text); border-color: var(--color-danger-text); }

@media (max-width: 640px) {
  .conflict-mask { padding: 0; align-items: flex-end; }
  .conflict-dialog { max-height: 90vh; border-radius: 16px 16px 0 0; }
  .cd-footer { flex-direction: column; }
  .cd-footer button { width: 100%; }
}
</style>