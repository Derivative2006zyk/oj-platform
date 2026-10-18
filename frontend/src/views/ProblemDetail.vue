<template>
  <main class="problem-page">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!problem" class="not-found">题目不存在</div>

    <div v-else :class="['content-wrapper', { 'focus-mode': isFocusMode }]">
      <!-- ========== 左栏：题目描述 ========== -->
      <div class="left-col">
        <article class="card problem-card">
          <header class="problem-header">
            <h1 class="title">{{ problem.title }}</h1>
            <div class="meta">
              <span class="tag">ID: {{ problem.id }}</span>
              <span class="tag">分类: {{ categoryName }}</span>
              <span class="tag">题型: {{ typeLabel }}</span>
              <span class="tag">难度: {{ '★'.repeat(problem.difficulty) }}</span>
            </div>
            <div v-if="problem.tags && problem.tags.length" class="tags">
              <span v-for="t in problem.tags" :key="t" class="tag-pill">{{ t }}</span>
            </div>
          </header>

          <section class="desc-section">
            <h2>题目描述</h2>
            <MarkdownRenderer :content="problem.description" />
          </section>

          <section v-if="problem.type === 'choice' && problem.options" class="desc-section">
            <h2>选项</h2>
            <div class="options">
              <div v-for="(opt, idx) in problem.options" :key="idx" class="option">
                <span class="option-key">{{ opt.key || String.fromCharCode(65 + idx) }}.</span>
                <span>{{ opt.content }}</span>
              </div>
            </div>
          </section>

          <section v-if="problem.type === 'fill_blank' && problem.blanks" class="desc-section">
            <h2>空位</h2>
            <div class="blanks">
              <div v-for="(b, idx) in problem.blanks" :key="idx" class="blank">
                <span>第 {{ b.blank_index || idx + 1 }} 空</span>
                <span v-if="b.match_rule" class="blank-rule">匹配: {{ b.match_rule }}</span>
              </div>
            </div>
          </section>

          <section
            v-if="problem.type === 'algorithm' && problem.test_cases && problem.test_cases.length"
            class="desc-section"
          >
            <h2>样例</h2>
            <div class="sample-card">
              <div
                v-for="(tc, idx) in problem.test_cases"
                :key="idx"
                class="sample-group"
              >
                <div class="sample-column">
                  <div class="sample-label">输入 #{{ idx + 1 }}</div>
                  <pre class="sample-content">{{ tc.input_data }}</pre>
                </div>
                <div class="sample-column">
                  <div class="sample-label">输出 #{{ idx + 1 }}</div>
                  <pre class="sample-content">{{ tc.expected_output }}</pre>
                </div>
              </div>
            </div>
          </section>

          <section
            v-if="problem.type === 'research' && problem.subprojects && problem.subprojects.length"
            class="desc-section"
          >
            <h2>子项目</h2>
            <div v-for="(sp, idx) in problem.subprojects" :key="idx" class="subproject">
              <h3>{{ sp.sort_order }}. {{ sp.title }}</h3>
              <MarkdownRenderer :content="sp.description" />
              <p v-if="sp.hint" class="subproject-hint">提示：{{ sp.hint }}</p>
            </div>
          </section>

          <section class="desc-section answer-section">
            <div class="section-header">
              <h2>答案</h2>
              <button v-if="!answerVisible" class="btn-ghost" @click="showAnswer">
                查看答案
              </button>
            </div>
            <div v-if="answerVisible" class="answer-box">
              <div v-if="answer && answer.answer">
                <h4>参考答案</h4>
                <MarkdownRenderer :content="answer.answer" />
              </div>
              <div v-if="answer && answer.explanation">
                <h4>解析</h4>
                <MarkdownRenderer :content="answer.explanation" />
              </div>
              <div v-if="!answer || (!answer.answer && !answer.explanation)" class="empty">
                暂无答案
              </div>
            </div>
          </section>
        </article>

        <!-- 我的提交历史 -->
        <section
          v-if="userStore.isLoggedIn"
          class="card history-card"
        >
          <div class="card-header history-header">
            <span>我的提交历史</span>
            <router-link to="/submissions" class="view-all-link">
              查看全部
            </router-link>
          </div>

          <div v-if="submissionsLoading" class="history-empty">加载中...</div>
          <div v-else-if="mySubmissions.length === 0" class="history-empty">
            暂无提交记录
          </div>

          <div v-else class="history-list">
            <div
              v-for="item in mySubmissions"
              :key="item.id"
              class="history-row"
            >
              <div class="history-left">
                <span :class="['status-badge', `status-${item.status}`]">
                  {{ statusLabel(item.status) }}
                </span>
                <span class="history-runtime">
                  {{ item.runtime_ms != null && item.runtime_ms > 0 ? item.runtime_ms + ' ms' : '—' }}
                </span>
              </div>

              <div class="history-mid">
                <span class="history-cases">
                  {{ item.passed_cases }} / {{ item.total_cases }}
                </span>
                <span class="history-lang">{{ languageLabel(item.language) }}</span>
              </div>

              <div class="history-right">
                {{ formatTime(item.created_at) }}
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- ========== 右栏：提交面板 ========== -->
      <aside class="right-col">
        <!-- 算法题：代码提交面板 -->
        <div v-if="problem.type === 'algorithm'" class="card submit-panel">
          <div class="card-header panel-header-with-action">
            <span>代码提交</span>
            <div class="header-actions">
              <button v-if="hasDraft" @click="onClearDraft" class="clear-btn">清空</button>
              <button class="btn-ghost focus-btn" @click="toggleFocusMode">
                {{ isFocusMode ? '退出横屏' : '横屏代码' }}
              </button>
            </div>
          </div>

          <div v-if="!userStore.isLoggedIn" class="login-tip">
            请先 <router-link to="/login">登录</router-link> 后提交
          </div>

          <template v-else>
            <div class="form-row">
              <label>语言</label>
              <select v-model="submitPanel.language" class="lang-select">
                <option value="python">Python 3</option>
                <option value="java">Java 17</option>
                <option value="cpp">C++ 17</option>
              </select>
            </div>

            <div class="editor-wrapper">
              <CodeEditor
                v-model="submitPanel.code"
                :language="submitPanel.language"
                height="100%"
              />
            </div>

            <div v-if="submitError" class="error">{{ submitError }}</div>

            <button
              class="btn-primary"
              :disabled="submitting || !submitPanel.code.trim()"
              @click="onSubmit"
            >
              {{ submitting ? '提交中...' : '提交' }}
            </button>

            <div v-if="currentSubmission" class="submission-result">
              <div class="result-row">
                <span class="result-label">状态</span>
                <span :class="['status-badge', `status-${currentSubmission.status}`]">
                  {{ statusLabel(currentSubmission.status) }}
                </span>
              </div>
              <div class="result-row">
                <span class="result-label">测试点</span>
                <span>{{ currentSubmission.passed_cases }} / {{ currentSubmission.total_cases }}</span>
              </div>
              <div
                v-if="currentSubmission.runtime_ms !== null && currentSubmission.runtime_ms !== undefined"
                class="result-row"
              >
                <span class="result-label">耗时</span>
                <span>{{ currentSubmission.runtime_ms }} ms</span>
              </div>
              <pre
                v-if="currentSubmission.error_message"
                class="error-message"
              >{{ currentSubmission.error_message }}</pre>
            </div>
          </template>
        </div>

        <!-- 选择题：作答面板 -->
        <div v-else-if="problem.type === 'choice'" class="card submit-panel">
          <div class="card-header panel-header-with-action">
            <span>选择题作答</span>
            <button v-if="hasDraft" @click="onClearDraft" class="clear-btn">清空</button>
          </div>

          <div v-if="!userStore.isLoggedIn" class="login-tip">
            请先 <router-link to="/login">登录</router-link> 后提交
          </div>

          <template v-else>
            <div class="choice-options">
              <label
                v-for="(opt, idx) in problem.options || []"
                :key="opt.key || idx"
                :class="['choice-option', { selected: choiceSelected === (opt.key || String.fromCharCode(65 + idx)) }]"
              >
                <input
                  type="radio"
                  name="choice-answer"
                  :value="opt.key || String.fromCharCode(65 + idx)"
                  v-model="choiceSelected"
                />
                <span class="choice-key">{{ opt.key || String.fromCharCode(65 + idx) }}.</span>
                <span class="choice-content">{{ opt.content }}</span>
              </label>
            </div>

            <div v-if="submitError" class="error">{{ submitError }}</div>

            <button
              class="btn-primary"
              :disabled="submitting || !choiceSelected"
              @click="onSubmitChoice"
            >
              {{ submitting ? '提交中...' : '提交' }}
            </button>

            <div v-if="currentSubmission" class="submission-result">
              <div class="result-row">
                <span class="result-label">状态</span>
                <span :class="['status-badge', `status-${currentSubmission.status}`]">
                  {{ statusLabel(currentSubmission.status) }}
                </span>
              </div>
              <div class="result-row">
                <span class="result-label">结果</span>
                <span>{{ currentSubmission.passed_cases }} / {{ currentSubmission.total_cases }}</span>
              </div>
              <pre
                v-if="currentSubmission.error_message"
                class="error-message"
              >{{ currentSubmission.error_message }}</pre>
            </div>
          </template>
        </div>

        <!-- 填空题：作答面板 -->
        <div v-else-if="problem.type === 'fill_blank'" class="card submit-panel">
          <div class="card-header panel-header-with-action">
            <span>填空题作答</span>
            <button v-if="hasDraft" @click="onClearDraft" class="clear-btn">清空</button>
          </div>

          <div v-if="!userStore.isLoggedIn" class="login-tip">
            请先 <router-link to="/login">登录</router-link> 后提交
          </div>

          <template v-else>
            <div class="blank-inputs">
              <div
                v-for="(b, idx) in problem.blanks || []"
                :key="idx"
                class="blank-input-item"
              >
                <label class="blank-input-label">
                  第 {{ b.blank_index || idx + 1 }} 空
                </label>
                <input
                  v-model="fillBlanks[idx]"
                  type="text"
                  class="blank-input"
                  :placeholder="`答案 ${idx + 1}`"
                  @keyup.enter="onSubmitFillBlank"
                />
              </div>
            </div>

            <div v-if="submitError" class="error">{{ submitError }}</div>

            <button
              class="btn-primary"
              :disabled="submitting || !hasAnyBlankFilled"
              @click="onSubmitFillBlank"
            >
              {{ submitting ? '提交中...' : '提交' }}
            </button>

            <div v-if="currentSubmission" class="submission-result">
              <div class="result-row">
                <span class="result-label">状态</span>
                <span :class="['status-badge', `status-${currentSubmission.status}`]">
                  {{ statusLabel(currentSubmission.status) }}
                </span>
              </div>
              <div class="result-row">
                <span class="result-label">正确空数</span>
                <span>{{ currentSubmission.passed_cases }} / {{ currentSubmission.total_cases }}</span>
              </div>
              <pre
                v-if="currentSubmission.error_message"
                class="error-message"
              >{{ currentSubmission.error_message }}</pre>
            </div>
          </template>
        </div>

        <!-- 证明题：作答面板 -->
        <div v-else-if="problem.type === 'proof'" class="card submit-panel">
          <div class="card-header panel-header-with-action">
            <span>证明题作答</span>
            <button v-if="hasDraft" @click="onClearDraft" class="clear-btn">清空</button>
          </div>

          <div v-if="!userStore.isLoggedIn" class="login-tip">
            请先 <router-link to="/login">登录</router-link> 后提交
          </div>

          <template v-else>
            <div class="proof-form">
              <div class="form-group">
                <label class="form-label">证明过程（文字）</label>
                <div class="proof-textarea-wrapper">
                  <textarea
                    v-model="proofText"
                    class="proof-textarea"
                    placeholder="可直接书写证明过程。"
                  ></textarea>
                </div>
              </div>

              <div class="form-group">
                <label class="form-label">上传图片（可多张）</label>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  multiple
                  class="proof-file-input"
                  @change="handleProofImageSelect"
                />
                <p v-if="proofUploading" class="proof-uploading">上传中...</p>
              </div>

              <div v-if="proofImages.length > 0" class="proof-image-grid">
                <div
                  v-for="img in proofImages"
                  :key="img.id"
                  class="proof-image-item"
                >
                  <img :src="img.url" :alt="`图片 ${img.id}`" />
                  <button
                    type="button"
                    class="proof-image-remove"
                    title="移除"
                    @click="removeProofImage(img.id)"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>

            <div v-if="submitError" class="error">{{ submitError }}</div>

            <button
              class="btn-primary"
              :disabled="submitting || !canSubmitProof"
              @click="onSubmitProof"
            >
              {{ submitting ? '提交中...' : '提交' }}
            </button>

            <div v-if="currentSubmission" class="submission-result">
              <div class="result-row">
                <span class="result-label">状态</span>
                <span :class="['status-badge', `status-${currentSubmission.status}`]">
                  {{ statusLabel(currentSubmission.status) }}
                </span>
              </div>
              <p class="proof-hint">
                证明题不自动判题，请自行核对或等待后续版本的人工/AI 评审。
              </p>
            </div>
          </template>
        </div>

        <!-- 题目信息 -->
        <div class="card info-card">
          <div class="card-header">
            <span>题目信息</span>
          </div>
          <div class="info-item">
            <span class="info-label">分类</span>
            <span class="info-value">{{ categoryName }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">题型</span>
            <span class="info-value">{{ typeLabel }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">难度</span>
            <span class="info-value">{{ '★'.repeat(problem.difficulty) }}</span>
          </div>
        </div>

        <router-link to="/" class="back-link">← 返回题目列表</router-link>
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Capacitor } from '@capacitor/core'
import { ScreenOrientation } from '@capacitor/screen-orientation'

import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { defineAsyncComponent } from 'vue'
const CodeEditor = defineAsyncComponent(() => import('../components/CodeEditor.vue'))
import { getProblemDetail, getProblemAnswer, type ProblemDetail } from '../api/problem'
import {
  submitCode,
  listProblemSubmissions,
  type SubmissionDetail,
} from '../api/submission'
import { uploadUserImage } from '../api/image'
import { openSubmissionWS, type SubmissionWSHandle, type WSMessage } from '../utils/ws'
import { useUserStore } from '../stores/user'
import { loadDraft, saveDraft, clearDraft, type DraftImage } from '../utils/draft'

const route = useRoute()
const userStore = useUserStore()

const problemId = computed(() => Number(route.params.id))

const loading = ref(true)
const problem = ref<ProblemDetail | null>(null)

const answer = ref<{ answer?: string | null; explanation?: string | null } | null>(null)
const answerVisible = ref(false)

// ===== 代码横屏模式 =====
const isFocusMode = ref(false)

// ===== 算法题提交面板状态 =====
const submitPanel = reactive({
  language: 'python',
  code: '',
})

// ===== 选择题状态 =====
const choiceSelected = ref<string>('')

// ===== 填空题状态 =====
const fillBlanks = ref<string[]>([])

const hasAnyBlankFilled = computed(() =>
  fillBlanks.value.some((s) => (s ?? '').trim() !== '')
)

// ===== 证明题状态 =====
const proofText = ref('')
const proofImages = ref<DraftImage[]>([])
const proofUploading = ref(false)

const canSubmitProof = computed(() => {
  return proofText.value.trim().length > 0 || proofImages.value.length > 0
})

// ===== 草稿状态 =====
const hasDraft = computed(() => {
  if (!problem.value) return false
  const t = problem.value.type
  if (t === 'algorithm') return submitPanel.code.trim() !== ''
  if (t === 'choice') return choiceSelected.value !== ''
  if (t === 'fill_blank') return hasAnyBlankFilled.value
  if (t === 'proof') return canSubmitProof.value
  return false
})

const submitting = ref(false)
const submitError = ref('')
const currentSubmission = ref<SubmissionDetail | null>(null)
const wsHandle = ref<SubmissionWSHandle | null>(null)

// ===== 提交历史 =====
interface HistoryItem {
  id: number
  language: string
  status: string
  passed_cases: number
  total_cases: number
  runtime_ms: number | null
  created_at: string
}

const mySubmissions = ref<HistoryItem[]>([])
const submissionsLoading = ref(false)

const categoryNames: Record<number, string> = {
  1: '算法',
  2: '数学',
  3: '物理',
  4: '英语',
  5: '其他',
}

const categoryName = computed(() => {
  if (!problem.value) return ''
  return categoryNames[problem.value.category_id] || `#${problem.value.category_id}`
})

const typeLabels: Record<string, string> = {
  algorithm: '算法题',
  choice: '选择题',
  fill_blank: '填空题',
  proof: '证明题',
  research: '科研项目',
}

const typeLabel = computed(() => {
  if (!problem.value) return ''
  return typeLabels[problem.value.type] || problem.value.type
})

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: '排队中',
    AC: '通过',
    WA: '答案错误',
    TLE: '时间超限',
    MLE: '内存超限',
    RE: '运行错误',
    CE: '编译错误',
    SUBMITTED: '已提交',
  }
  return map[status] || status
}

function languageLabel(lang: string): string {
  if (lang === 'choice') return '选择题'
  if (lang === 'fill_blank') return '填空题'
  if (lang === 'proof') return '证明题'
  if (lang === 'python') return 'Python'
  if (lang === 'java') return 'Java'
  if (lang === 'cpp') return 'C++'
  return lang
}

async function loadProblem() {
  loading.value = true
  try {
    const data = await getProblemDetail(problemId.value)
    problem.value = data

    const draft = loadDraft(data.id)

    // 填空题初始化输入数组
    if (data.type === 'fill_blank') {
      const total = Array.isArray(data.blanks) ? data.blanks.length : 0
      const saved = Array.isArray(draft.fillBlanks) ? draft.fillBlanks : []
      fillBlanks.value = new Array(total).fill('').map((_, i) => saved[i] ?? '')
    } else {
      fillBlanks.value = []
    }

    // 恢复草稿：算法题
    if (data.type === 'algorithm') {
      submitPanel.language = draft.language || 'python'
      submitPanel.code = draft.code || ''
    } else {
      submitPanel.language = 'python'
      submitPanel.code = ''
    }

    // 恢复草稿：选择题
    if (data.type === 'choice') {
      choiceSelected.value = draft.choiceSelected || ''
    } else {
      choiceSelected.value = ''
    }

    // 恢复草稿：证明题
    if (data.type === 'proof') {
      proofText.value = draft.proofText || ''
      proofImages.value = Array.isArray(draft.proofImages) ? draft.proofImages : []
    } else {
      proofText.value = ''
      proofImages.value = []
    }
  } catch (e) {
    console.error('加载题目失败', e)
    problem.value = null
    fillBlanks.value = []
    proofText.value = ''
    proofImages.value = []
    submitPanel.code = ''
    choiceSelected.value = ''
  } finally {
    loading.value = false
  }
}

async function showAnswer() {
  try {
    const data = await getProblemAnswer(problemId.value)
    answer.value = data
    answerVisible.value = true
  } catch (e) {
    console.error('加载答案失败', e)
  }
}

async function loadMySubmissions() {
  if (!userStore.isLoggedIn) {
    mySubmissions.value = []
    return
  }

  submissionsLoading.value = true
  try {
    const data = await listProblemSubmissions(problemId.value, 1, 3)
    mySubmissions.value = data.items || []
  } catch (e) {
    console.error('加载提交历史失败', e)
    mySubmissions.value = []
  } finally {
    submissionsLoading.value = false
  }
}

function formatTime(s: string): string {
  if (!s) return '-'
  try {
    // 如果后端返回的时间没有带 'Z'（UTC 标识），手动补上，让浏览器按 UTC 解析并转换为本地时间
    let timeStr = s
    if (!timeStr.endsWith('Z') && !timeStr.includes('+')) {
      timeStr = timeStr.replace(' ', 'T') + 'Z'
    }
    const d = new Date(timeStr)
    if (isNaN(d.getTime())) return s
    
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return s
  }
}

// ===== 横屏代码模式 =====
async function toggleFocusMode() {
  // 如果当前是准备进入横屏，且是手机设备，给出提示
  if (!isFocusMode.value) {
    const isPhone = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
                    && navigator.userAgent.indexOf('iPad') === -1
                    
    if (isPhone) {
      if (!window.confirm('提示：因手机屏幕较小，软键盘会遮挡部分视野，推荐在平板或电脑端使用横屏代码模式。\n\n是否仍要进入？')) {
        return // 用户取消，不进入横屏
      }
    }
  }

  isFocusMode.value = !isFocusMode.value
  
  if (Capacitor.isNativePlatform()) {
    try {
      if (isFocusMode.value) {
        await ScreenOrientation.lock({ orientation: 'landscape' })
      } else {
        await ScreenOrientation.unlock()
      }
    } catch (e) {
      console.warn('屏幕旋转失败', e)
    }
  }
}

// ===== 草稿保存 =====
let draftTimer: number | null = null

function scheduleDraftSave() {
  if (!problem.value) return
  if (draftTimer) window.clearTimeout(draftTimer)
  draftTimer = window.setTimeout(() => {
    if (!problem.value) return
    const id = problem.value.id
    const t = problem.value.type
    if (t === 'algorithm') {
      saveDraft(id, { language: submitPanel.language, code: submitPanel.code })
    } else if (t === 'choice') {
      saveDraft(id, { choiceSelected: choiceSelected.value })
    } else if (t === 'fill_blank') {
      saveDraft(id, { fillBlanks: [...fillBlanks.value] })
    } else if (t === 'proof') {
      saveDraft(id, {
        proofText: proofText.value,
        proofImages: [...proofImages.value],
      })
    }
  }, 400)
}

function onClearDraft() {
  if (!problem.value) return
  clearDraft(problem.value.id)

  const t = problem.value.type
  if (t === 'algorithm') {
    submitPanel.code = ''
  } else if (t === 'choice') {
    choiceSelected.value = ''
  } else if (t === 'fill_blank') {
    const total = Array.isArray(problem.value.blanks) ? problem.value.blanks.length : 0
    fillBlanks.value = new Array(total).fill('')
  } else if (t === 'proof') {
    proofText.value = ''
    proofImages.value = []
  }
}

// 监听所有输入变化，debounce 保存草稿
watch(
  [
    () => submitPanel.language,
    () => submitPanel.code,
    choiceSelected,
    fillBlanks,
    proofText,
    proofImages,
  ],
  scheduleDraftSave,
  { deep: true }
)

// 组件卸载时立即保存一次
onUnmounted(() => {
  if (draftTimer) {
    window.clearTimeout(draftTimer)
    draftTimer = null
  }
  if (problem.value) {
    const id = problem.value.id
    const t = problem.value.type
    if (t === 'algorithm') {
      saveDraft(id, { language: submitPanel.language, code: submitPanel.code })
    } else if (t === 'choice') {
      saveDraft(id, { choiceSelected: choiceSelected.value })
    } else if (t === 'fill_blank') {
      saveDraft(id, { fillBlanks: [...fillBlanks.value] })
    } else if (t === 'proof') {
      saveDraft(id, {
        proofText: proofText.value,
        proofImages: [...proofImages.value],
      })
    }
  }
  if (wsHandle.value) {
    wsHandle.value.close()
    wsHandle.value = null
  }
  
  // 如果卸载时还在强制横屏，解除锁定
  if (isFocusMode.value && Capacitor.isNativePlatform()) {
    ScreenOrientation.unlock().catch(() => {})
  }
})

// ===== 算法题提交 =====
async function onSubmit() {
  submitError.value = ''

  if (!userStore.isLoggedIn) {
    submitError.value = '请先登录'
    return
  }

  if (!submitPanel.code.trim()) {
    submitError.value = '代码不能为空'
    return
  }

  submitting.value = true

  try {
    const sub = await submitCode({
      problem_id: problemId.value,
      code: submitPanel.code,
      language: submitPanel.language,
    })

    currentSubmission.value = sub
    openWS(sub.id)
    loadMySubmissions()
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) {
      submitError.value = '登录已过期，请重新登录'
    } else {
      submitError.value = e?.response?.data?.detail || '提交失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

// ===== 选择题提交 =====
async function onSubmitChoice() {
  submitError.value = ''

  if (!userStore.isLoggedIn) {
    submitError.value = '请先登录'
    return
  }
  if (!choiceSelected.value) {
    submitError.value = '请选择一个选项'
    return
  }

  submitting.value = true

  try {
    const sub = await submitCode({
      problem_id: problemId.value,
      language: 'choice',
      answer_data: { selected: choiceSelected.value },
    })

    currentSubmission.value = sub
    loadMySubmissions()
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) {
      submitError.value = '登录已过期，请重新登录'
    } else {
      submitError.value = e?.response?.data?.detail || '提交失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

// ===== 填空题提交 =====
async function onSubmitFillBlank() {
  submitError.value = ''

  if (!userStore.isLoggedIn) {
    submitError.value = '请先登录'
    return
  }
  if (!hasAnyBlankFilled.value) {
    submitError.value = '请至少填写一个空'
    return
  }

  submitting.value = true

  try {
    const sub = await submitCode({
      problem_id: problemId.value,
      language: 'fill_blank',
      answer_data: { blanks: fillBlanks.value.map((s) => (s ?? '').trim()) },
    })

    currentSubmission.value = sub
    loadMySubmissions()
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) {
      submitError.value = '登录已过期，请重新登录'
    } else {
      submitError.value = e?.response?.data?.detail || '提交失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

// ===== 证明题提交 =====
async function handleProofImageSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  proofUploading.value = true
  try {
    for (const file of Array.from(input.files)) {
      if (file.size > 5 * 1024 * 1024) {
        submitError.value = `图片 ${file.name} 超过 5MB`
        continue
      }
      const res = await uploadUserImage(file)
      proofImages.value.push({ id: res.id, url: res.url })
    }
    submitError.value = ''
  } catch (e: any) {
    submitError.value = e?.response?.data?.detail || '图片上传失败'
  } finally {
    proofUploading.value = false
    input.value = ''
  }
}

function removeProofImage(id: number) {
  proofImages.value = proofImages.value.filter((img) => img.id !== id)
}

async function onSubmitProof() {
  submitError.value = ''

  if (!userStore.isLoggedIn) {
    submitError.value = '请先登录'
    return
  }
  if (!canSubmitProof.value) {
    submitError.value = '请填写证明过程或上传图片'
    return
  }

  submitting.value = true

  try {
    const sub = await submitCode({
      problem_id: problemId.value,
      language: 'proof',
      answer_data: {
        text: proofText.value.trim(),
        images: proofImages.value.map((img) => img.id),
      },
    })

    currentSubmission.value = sub
    loadMySubmissions()
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401) {
      submitError.value = '登录已过期，请重新登录'
    } else {
      submitError.value = e?.response?.data?.detail || '提交失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

function openWS(submissionId: number) {
  if (wsHandle.value) {
    wsHandle.value.close()
    wsHandle.value = null
  }

  wsHandle.value = openSubmissionWS(
    submissionId,
    (msg: WSMessage) => {
      if (!currentSubmission.value) return
      if (msg.submission_id !== currentSubmission.value.id) return

      currentSubmission.value = {
        ...currentSubmission.value,
        status: msg.status,
        passed_cases: msg.passed_cases ?? currentSubmission.value.passed_cases,
        total_cases: msg.total_cases ?? currentSubmission.value.total_cases,
        runtime_ms: msg.runtime_ms ?? currentSubmission.value.runtime_ms,
      }

      if (msg.type === 'judged') {
        if (wsHandle.value) {
          wsHandle.value.close()
          wsHandle.value = null
        }
        loadMySubmissions()

        const token = localStorage.getItem('oj_token')
        if (token) {
          import('../utils/tauri').then(({ refreshTrayFromBackend }) => {
            refreshTrayFromBackend(token).catch(() => {})
          })
        }
      }
    },
    (e) => {
      console.warn('WS error', e)
    }
  )
}

onMounted(() => {
  loadProblem()
  loadMySubmissions()
})
</script>

<style scoped>
.problem-page {
  padding: var(--spacing-xl) 0;
}

.loading,
.not-found {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-muted);
}

/* ===== 两栏布局 ===== */
.content-wrapper {
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  display: flex;
  gap: clamp(24px, 4vw, 40px);
  align-items: flex-start;
  flex-wrap: wrap;
}

.left-col {
  flex: 1 1 500px;
  min-width: 0;
}

.right-col {
  flex: 0 0 340px;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* ===== 沉浸式横屏代码模式 ===== */
.content-wrapper.focus-mode {
  flex-wrap: nowrap;
  /* 使用 dvh 适配动态视口高度 */
  height: calc(100dvh - 56px);
  padding: 0;
  margin: 0;
  gap: 0;
}

.content-wrapper.focus-mode .left-col {
  display: none !important;
}

.content-wrapper.focus-mode .right-col {
  flex: 1 1 100% !important;
  height: 100%;
  gap: 0;
}

.content-wrapper.focus-mode .submit-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 0;
  box-shadow: none;
  background: var(--color-bg-card);
}

/* 注意：这里千万不能隐藏 card-header */
.content-wrapper.focus-mode .submit-panel > .card-header {
  display: flex !important;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg-card);
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border-light);
  flex-shrink: 0;
  /* 防止被上方导航栏遮挡 */
  z-index: 10;
}

/* 隐藏横屏下不需要的辅助元素 */
.content-wrapper.focus-mode .form-row,
.content-wrapper.focus-mode .info-card,
.content-wrapper.focus-mode .back-link,
.content-wrapper.focus-mode .login-tip {
  display: none !important;
}

/* 编辑器占满中间全部剩余空间 */
.content-wrapper.focus-mode .editor-wrapper {
  flex: 1;
  min-height: 0;
  margin: 0;
  height: auto !important;
  max-height: none !important;
  border-radius: 0;
  border: none;
}

/* 提交按钮和结果固定在底部并留出空间 */
.content-wrapper.focus-mode > .submit-panel > .btn-primary {
  margin: 12px 16px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
  padding: 12px 24px;
}

.content-wrapper.focus-mode .submission-result {
  margin: 0 16px 12px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .content-wrapper {
    gap: var(--spacing-lg);
  }
  .right-col {
    flex: 1 1 100%;
  }
}

/* ===== 卡片基础 ===== */
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-card-hover);
}

.card-header {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
  font-size: var(--font-size-small);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.panel-header-with-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.focus-btn {
  padding: 2px 10px;
  font-size: 12px;
  height: 24px;
}

.clear-btn {
  padding: 2px 8px;
  font-size: 12px;
  color: var(--color-text-muted);
  background: transparent;
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.clear-btn:hover {
  color: var(--color-danger-text);
  border-color: var(--color-danger-text);
}

/* ===== 题目卡片 ===== */
.problem-card {
  padding: var(--spacing-xl);
}

.problem-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border-light);
}

.title {
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.tag {
  padding: 2px 10px;
  background: var(--color-tag-bg);
  color: var(--color-tag-text);
  font-size: var(--font-size-small);
  border-radius: 12px;
  font-weight: 500;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-pill {
  padding: 2px 10px;
  background: #eff6ff;
  color: #1e40af;
  font-size: var(--font-size-small);
  border-radius: 12px;
}

.desc-section {
  margin-bottom: var(--spacing-lg);
}

.desc-section h2 {
  font-size: var(--font-size-subtitle);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-sm);
}

.desc-section h3 {
  font-size: 15px;
  margin: 0 0 var(--spacing-sm);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-sm);
}

.section-header h2 {
  margin: 0;
}

.options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.option {
  padding: 10px 14px;
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
}

.option-key {
  font-weight: 600;
  margin-right: 8px;
  color: var(--color-primary);
}

.blanks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.blank {
  display: flex;
  gap: var(--spacing-md);
  font-size: var(--font-size-body);
}

.blank-rule {
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
}

.sample-card {
  background: var(--color-sample-bg);
  border: 1px solid var(--color-sample-code-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.sample-group {
  display: flex;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.sample-group + .sample-group {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px dashed var(--color-border);
}

.sample-column {
  flex: 1;
  min-width: 180px;
}

.sample-label {
  font-size: var(--font-size-small);
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}

.sample-content {
  font-family: var(--font-family-mono);
  font-size: 13px;
  background: var(--color-sample-code-bg);
  border: 1px solid var(--color-sample-code-border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.7;
}

.subproject {
  margin-bottom: var(--spacing-md);
  padding-left: var(--spacing-md);
  border-left: 3px solid var(--color-primary);
}

.subproject-hint {
  margin-top: var(--spacing-sm);
  padding: 8px 12px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  font-size: 13px;
  border-radius: var(--radius-md);
}

.answer-box {
  padding: var(--spacing-md);
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
}

.answer-box h4 {
  margin: 12px 0 8px;
  font-size: 15px;
}

.answer-box h4:first-child {
  margin-top: 0;
}

.answer-box .empty {
  color: var(--color-text-muted);
  text-align: center;
  padding: 20px;
}

.history-card {
  margin-top: var(--spacing-lg);
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-transform: none;
  letter-spacing: 0;
  font-size: var(--font-size-body);
}

.view-all-link {
  color: var(--color-primary);
  font-size: var(--font-size-small);
  font-weight: 500;
}

.view-all-link:hover {
  text-decoration: underline;
}

.history-empty {
  text-align: center;
  padding: 32px 20px;
  color: var(--color-text-muted);
  font-size: var(--font-size-body);
}

.history-list {
  padding: var(--spacing-sm) var(--spacing-md) var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.history-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: var(--color-sample-bg);
  transition: background 0.15s;
}

.history-row:hover {
  background: var(--color-primary-light);
}

.history-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 70px;
  flex-shrink: 0;
}

.history-runtime {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-family-mono);
}

.history-mid {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  min-width: 0;
}

.history-cases {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
}

.history-lang {
  display: inline-block;
  padding: 1px 8px;
  background: white;
  border: 1px solid var(--color-border-light);
  border-radius: 10px;
  font-size: 11px;
  color: var(--color-text-secondary);
  font-family: var(--font-family-mono);
}

.history-right {
  font-size: 12px;
  color: var(--color-text-muted);
  flex-shrink: 0;
}

@media (max-width: 600px) {
  .history-row {
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .history-left {
    flex-direction: row;
    gap: 8px;
    min-width: auto;
    width: 100%;
  }

  .history-right {
    width: 100%;
    text-align: left;
  }
}

.submit-panel {
  overflow: visible;
}

.submit-panel > .form-row,
.submit-panel > .code-input,
.submit-panel > .btn-primary,
.submit-panel > .error,
.submit-panel > .submission-result,
.submit-panel > .login-tip {
  margin-left: var(--spacing-md);
  margin-right: var(--spacing-md);
}

.login-tip {
  margin: var(--spacing-md);
  padding: 12px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  border-radius: var(--radius-md);
  font-size: 13px;
}

.login-tip a {
  color: var(--color-primary);
  font-weight: 600;
}

.form-row {
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-sm);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-body);
}

.form-row label {
  color: var(--color-text-secondary);
}

.lang-select {
  padding: 4px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 13px;
  background: var(--color-bg-card);
  cursor: pointer;
  outline: none;
}

.btn-primary {
  margin-top: var(--spacing-sm);
  padding: 8px 24px;
  background: var(--color-primary);
  color: var(--color-primary-text);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  background: var(--color-primary-disabled);
  cursor: not-allowed;
}

.btn-ghost {
  padding: 4px 12px;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-ghost:hover {
  background: rgba(79, 70, 229, 0.06);
}

.error {
  margin-top: var(--spacing-sm);
  padding: 8px 12px;
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  font-size: 13px;
  border-radius: var(--radius-md);
}

.submission-result {
  margin-top: var(--spacing-md);
  margin-bottom: var(--spacing-md);
  padding: 12px;
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
}

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: var(--font-size-body);
}

.result-row:last-child {
  margin-bottom: 0;
}

.result-label {
  color: var(--color-text-secondary);
}

.status-badge {
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: 13px;
}

.status-PENDING { background: var(--color-neutral-bg); color: var(--color-neutral-text); }
.status-AC { background: var(--color-success-bg); color: var(--color-success-text); }
.status-WA { background: var(--color-danger-bg); color: var(--color-danger-text); }
.status-TLE { background: var(--color-warning-bg); color: var(--color-warning-text); }
.status-MLE { background: var(--color-warning-bg); color: var(--color-warning-text); }
.status-RE { background: var(--color-danger-bg); color: var(--color-danger-text); }
.status-CE { background: var(--color-danger-bg); color: var(--color-danger-text); }
.status-SUBMITTED { background: var(--color-primary-light); color: var(--color-primary); }

.error-message {
  margin-top: 8px;
  padding: 8px 12px;
  background: #1f2937;
  color: #f9fafb;
  font-size: 12px;
  font-family: var(--font-family-mono);
  border-radius: var(--radius-md);
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.info-card {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-body);
}

.info-label {
  color: var(--color-text-secondary);
}

.info-value {
  font-weight: 500;
  color: var(--color-text-primary);
}

.back-link {
  display: inline-block;
  padding: 8px 16px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-body);
  border-radius: var(--radius-md);
  transition: background 0.2s, color 0.2s;
}

.back-link:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-primary);
}

.editor-wrapper {
  margin: 0 var(--spacing-md) var(--spacing-sm);
  border-radius: var(--radius-md);
  resize: both;
  overflow: auto;
  min-width: 240px;
  max-width: 100%;
  min-height: 200px;
  max-height: 800px;
  height: 360px;
}

.choice-options {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin: var(--spacing-md);
}

.choice-option {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  padding: 10px 14px;
  background: var(--color-sample-bg);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.choice-option:hover {
  border-color: var(--color-primary);
}

.choice-option.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.choice-option input[type="radio"] {
  margin-top: 3px;
  flex-shrink: 0;
}

.choice-key {
  font-weight: 600;
  color: var(--color-primary);
  flex-shrink: 0;
}

.choice-content {
  color: var(--color-text-primary);
  font-size: var(--font-size-body);
  line-height: 1.5;
  word-break: break-word;
}

.blank-inputs {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  margin: var(--spacing-md);
}

.blank-input-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.blank-input-label {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.blank-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-family: var(--font-family-mono);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.blank-input:focus {
  border-color: var(--color-primary);
}

.proof-form {
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.proof-form .form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.proof-form .form-label {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
  font-weight: 500;
}

.proof-textarea-wrapper {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  resize: both;
  overflow: auto;
  width: 100%;
  min-width: 200px;
  max-width: 100%;
  min-height: 140px;
  max-height: 600px;
  height: 200px;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.proof-textarea-wrapper:focus-within {
  border-color: var(--color-primary);
}

.proof-textarea {
  width: 100%;
  height: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-family: inherit;
  background: transparent;
  color: var(--color-text-primary);
  box-sizing: border-box;
  outline: none;
  resize: none;
  display: block;
}

.proof-file-input {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.proof-uploading {
  font-size: 12px;
  color: var(--color-primary);
  margin: 4px 0 0;
}

.proof-image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: var(--spacing-sm);
}

.proof-image-item {
  position: relative;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-sample-bg);
  aspect-ratio: 1 / 1;
}

.proof-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.proof-image-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.proof-image-remove:hover {
  background: rgba(0, 0, 0, 0.85);
}

.proof-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}
</style>