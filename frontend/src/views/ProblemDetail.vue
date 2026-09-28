<template>
  <div class="problem-detail">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!problem" class="not-found">题目不存在</div>
    <div v-else class="content">
      <!-- ===== 标题区 ===== -->
      <div class="header">
        <h1>{{ problem.title }}</h1>
        <div class="meta">
          <span class="badge">ID: {{ problem.id }}</span>
          <span class="badge">分类: {{ categoryName }}</span>
          <span class="badge">题型: {{ typeLabel }}</span>
          <span class="badge">难度: {{ '★'.repeat(problem.difficulty) }}</span>
        </div>
        <div v-if="problem.tags && problem.tags.length" class="tags">
          <span v-for="t in problem.tags" :key="t" class="tag">{{ t }}</span>
        </div>
      </div>

      <!-- ===== 题目描述 ===== -->
      <section class="section">
        <h2>题目描述</h2>
        <MarkdownRenderer :content="problem.description" />
      </section>

      <!-- ===== 选择题选项 ===== -->
      <section v-if="problem.type === 'choice' && problem.options" class="section">
        <h2>选项</h2>
        <div class="options">
          <div v-for="(opt, idx) in problem.options" :key="idx" class="option">
            <span class="key">{{ opt.key || String.fromCharCode(65 + idx) }}.</span>
            <span>{{ opt.content }}</span>
          </div>
        </div>
      </section>

      <!-- ===== 填空题 ===== -->
      <section v-if="problem.type === 'fill_blank' && problem.blanks" class="section">
        <h2>空位</h2>
        <div class="blanks">
          <div v-for="(b, idx) in problem.blanks" :key="idx" class="blank">
            <span>第 {{ b.blank_index || idx + 1 }} 空</span>
            <span v-if="b.match_rule" class="rule">匹配: {{ b.match_rule }}</span>
          </div>
        </div>
      </section>

      <!-- ===== 算法题示例 ===== -->
      <section v-if="problem.type === 'algorithm' && problem.test_cases && problem.test_cases.length" class="section">
        <h2>示例</h2>
        <div v-for="(tc, idx) in problem.test_cases" :key="idx" class="test-case">
          <div class="tc-title">示例 {{ idx + 1 }}</div>
          <div class="tc-block">
            <div class="tc-label">输入</div>
            <pre>{{ tc.input_data }}</pre>
          </div>
          <div class="tc-block">
            <div class="tc-label">输出</div>
            <pre>{{ tc.expected_output }}</pre>
          </div>
        </div>
      </section>

      <!-- ===== 科研题子项目 ===== -->
      <section v-if="problem.type === 'research' && problem.subprojects && problem.subprojects.length" class="section">
        <h2>子项目</h2>
        <div v-for="(sp, idx) in problem.subprojects" :key="idx" class="subproject">
          <h3>{{ sp.sort_order }}. {{ sp.title }}</h3>
          <MarkdownRenderer :content="sp.description" />
          <p v-if="sp.hint" class="hint">提示：{{ sp.hint }}</p>
        </div>
      </section>

      <!-- ===== 答案 ===== -->
      <section class="section">
        <div class="section-header">
          <h2>答案</h2>
          <button v-if="!answerVisible" class="btn-secondary" @click="showAnswer">
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

      <!-- ===== 代码提交面板 ===== -->
      <section v-if="problem.type === 'algorithm'" class="section submit-section">
        <h2>提交代码</h2>

        <div v-if="!userStore.isLoggedIn" class="login-tip">
          请先 <router-link to="/login">登录</router-link> 后提交
        </div>

        <template v-else>
          <div class="form-row">
            <label>语言：</label>
            <select v-model="submitPanel.language">
              <option value="python">Python 3</option>
              <option value="java">Java 17</option>
              <option value="cpp">C++ 17</option>
            </select>
          </div>

          <textarea
            v-model="submitPanel.code"
            class="code-input"
            placeholder="在此粘贴代码..."
            rows="14"
          ></textarea>

          <div v-if="submitError" class="error">{{ submitError }}</div>

          <button
            class="btn-primary"
            :disabled="submitting || !submitPanel.code.trim()"
            @click="onSubmit"
          >
            {{ submitting ? '提交中...' : '提交' }}
          </button>

          <!-- 提交结果 -->
          <div v-if="currentSubmission" class="submission-result">
            <div class="result-row">
              <span>状态：</span>
              <span :class="['status-badge', `status-${currentSubmission.status}`]">
                {{ statusLabel(currentSubmission.status) }}
              </span>
            </div>
            <div class="result-row">
              <span>测试点：</span>
              <span>{{ currentSubmission.passed_cases }} / {{ currentSubmission.total_cases }}</span>
            </div>
            <div v-if="currentSubmission.runtime_ms !== null && currentSubmission.runtime_ms !== undefined" class="result-row">
              <span>耗时：</span>
              <span>{{ currentSubmission.runtime_ms }} ms</span>
            </div>
            <pre v-if="currentSubmission.error_message" class="error-message">{{ currentSubmission.error_message }}</pre>
          </div>
        </template>
      </section>

      <!-- ===== 操作按钮 ===== -->
      <div class="actions">
        <router-link class="btn-secondary" to="/">返回列表</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'

import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import { getProblemDetail, getProblemAnswer, type ProblemDetail } from '../api/problem'
import { submitCode, type SubmissionDetail } from '../api/submission'
import { openSubmissionWS, type SubmissionWSHandle, type WSMessage } from '../utils/ws'
import { useUserStore } from '../stores/user'

const route = useRoute()
const userStore = useUserStore()

const problemId = computed(() => Number(route.params.id))

const loading = ref(true)
const problem = ref<ProblemDetail | null>(null)

const answer = ref<{ answer?: string | null; explanation?: string | null } | null>(null)
const answerVisible = ref(false)

// ===== 提交面板状态 =====
const submitPanel = reactive({
  language: 'python',
  code: '',
})

const submitting = ref(false)
const submitError = ref('')
const currentSubmission = ref<SubmissionDetail | null>(null)
const wsHandle = ref<SubmissionWSHandle | null>(null)

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
  algorithm: '算法',
  choice: '选择',
  fill_blank: '填空',
  proof: '证明',
  research: '科研',
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
  }
  return map[status] || status
}

async function loadProblem() {
  loading.value = true
  try {
    const data = await getProblemDetail(problemId.value)
    problem.value = data
  } catch (e) {
    console.error('加载题目失败', e)
    problem.value = null
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
  // 关旧连接
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
      }
    },
    (e) => {
      console.warn('WS error', e)
    }
  )
}

onMounted(() => {
  loadProblem()
})

onUnmounted(() => {
  if (wsHandle.value) {
    wsHandle.value.close()
    wsHandle.value = null
  }
})
</script>

<style scoped>
.problem-detail {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.loading,
.not-found {
  text-align: center;
  padding: 60px 0;
  color: #666;
}

.header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.header h1 {
  margin: 0 0 12px;
  font-size: 24px;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #374151;
  font-size: 12px;
  border-radius: 3px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  padding: 2px 8px;
  background: #eff6ff;
  color: #1e40af;
  font-size: 12px;
  border-radius: 3px;
}

.section {
  margin-bottom: 32px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section h2 {
  margin: 0 0 12px;
  font-size: 18px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h2 {
  margin: 0;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option {
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 14px;
}

.option .key {
  font-weight: 600;
  margin-right: 8px;
}

.blanks {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.blank {
  display: flex;
  gap: 12px;
  font-size: 14px;
}

.blank .rule {
  color: #666;
  font-size: 12px;
}

.test-case {
  margin-bottom: 16px;
}

.tc-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}

.tc-block {
  margin-bottom: 8px;
}

.tc-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.tc-block pre {
  margin: 0;
  padding: 8px 12px;
  background: #1f2937;
  color: #f9fafb;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.subproject {
  margin-bottom: 20px;
  padding-left: 12px;
  border-left: 3px solid #4f46e5;
}

.subproject h3 {
  margin: 0 0 8px;
  font-size: 16px;
}

.subproject .hint {
  margin-top: 8px;
  padding: 6px 10px;
  background: #fef3c7;
  color: #92400e;
  font-size: 13px;
  border-radius: 4px;
}

.answer-box {
  padding: 12px;
  background: #f9fafb;
  border-radius: 4px;
}

.answer-box h4 {
  margin: 12px 0 8px;
  font-size: 15px;
}

.answer-box h4:first-child {
  margin-top: 0;
}

.answer-box .empty {
  color: #999;
  text-align: center;
  padding: 20px;
}

/* ===== 提交面板 ===== */
.submit-section {
  margin-bottom: 32px;
}

.login-tip {
  padding: 12px;
  background: #fef3c7;
  color: #92400e;
  border-radius: 4px;
  font-size: 14px;
}

.login-tip a {
  color: #4f46e5;
  font-weight: 600;
}

.form-row {
  margin-bottom: 12px;
  font-size: 14px;
}

.form-row select {
  padding: 6px 10px;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  font-size: 14px;
}

.code-input {
  width: 100%;
  padding: 12px;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  box-sizing: border-box;
  resize: vertical;
  outline: none;
}

.code-input:focus {
  border-color: #4f46e5;
}

.btn-primary {
  margin-top: 12px;
  padding: 8px 24px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}

.btn-primary:disabled {
  background: #a5b4fc;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 6px 14px;
  background: white;
  color: #374151;
  border: 1px solid #d0d5dd;
  border-radius: 4px;
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
}

.btn-secondary:hover {
  border-color: #4f46e5;
  color: #4f46e5;
}

.error {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 13px;
  border-radius: 4px;
}

.submission-result {
  margin-top: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 4px;
}

.result-row {
  margin-bottom: 8px;
  font-size: 14px;
}

.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 3px;
  font-weight: 500;
  font-size: 13px;
}

.status-PENDING { background: #e5e7eb; color: #374151; }
.status-AC { background: #d1fae5; color: #065f46; }
.status-WA { background: #fee2e2; color: #991b1b; }
.status-TLE { background: #fef3c7; color: #92400e; }
.status-MLE { background: #fef3c7; color: #92400e; }
.status-RE { background: #fee2e2; color: #991b1b; }
.status-CE { background: #fee2e2; color: #991b1b; }

.error-message {
  margin-top: 8px;
  padding: 8px 12px;
  background: #1f2937;
  color: #f9fafb;
  font-size: 12px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
</style>