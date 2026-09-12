<template>
  <div class="problem-detail" v-if="problem">
    <h1>{{ problem.title }}</h1>

    <div class="meta">
      <span>难度：{{ '★'.repeat(problem.difficulty) }}</span>
      <span>题型：{{ typeLabel(problem.type) }}</span>
      <span v-for="tag in problem.tags" :key="tag" class="tag">{{ tag }}</span>
    </div>

    <!-- 题目描述 -->
    <h2>题目描述</h2>
    <MarkdownRenderer :content="problem.description" />

    <!-- 算法题：示例测试用例 -->
    <div v-if="problem.type === 'algorithm' && problem.test_cases.length > 0">
      <h2>示例</h2>
      <div v-for="(tc, idx) in problem.test_cases" :key="idx" class="test-case">
        <p><strong>输入：</strong></p>
        <pre>{{ tc.input_data }}</pre>
        <p><strong>输出：</strong></p>
        <pre>{{ tc.expected_output }}</pre>
      </div>
    </div>

    <!-- 选择题：选项 -->
    <div v-if="problem.type === 'choice' && problem.options">
      <h2>选项</h2>
      <div v-for="opt in problem.options" :key="opt.key" class="option">
        <strong>{{ opt.key }}.</strong> {{ opt.content }}
      </div>
    </div>

    <!-- 填空题：填空位置 -->
    <div v-if="problem.type === 'fill_blank' && problem.blanks">
      <h2>填空</h2>
      <p>共 {{ problem.blanks.length }} 个空</p>
    </div>

    <!-- 科研项目：子项目列表 -->
    <div v-if="problem.type === 'research' && problem.subprojects.length > 0">
      <h2>子项目（{{ problem.subprojects.length }}个）</h2>
      <div v-for="(sp, idx) in problem.subprojects" :key="sp.id" class="subproject">
        <h3>子项目{{ idx + 1 }}：{{ sp.title }}</h3>
        <MarkdownRenderer :content="sp.description" />

        <div v-if="sp.hint" class="hint">
          <strong>思路提示：</strong>
          <MarkdownRenderer :content="sp.hint" />
        </div>

        <div v-if="sp.reference_links.length > 0" class="refs">
          <strong>参考资源：</strong>
          <div v-for="(ref, i) in sp.reference_links" :key="i" class="ref-item">
            <a :href="ref.url" target="_blank" rel="noopener noreferrer">{{ ref.title }}</a>
            <span v-if="ref.note" class="ref-note"> - {{ ref.note }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看答案 -->
    <button @click="toggleAnswer" class="answer-btn">
      {{ showAnswer ? '隐藏答案' : '查看答案' }}
    </button>

    <div v-if="showAnswer && answer" class="answer-block">
      <h2>答案</h2>
      <MarkdownRenderer :content="answer.answer || '（无答案）'" />

      <div v-if="answer.explanation">
        <h2>解析</h2>
        <MarkdownRenderer :content="answer.explanation" />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <button @click="goEdit" class="edit-btn">编辑</button>
      <button @click="handleDelete" class="delete-btn">删除</button>
      <button @click="goBack" class="back-btn">返回列表</button>
    </div>
  </div>

  <div v-else class="loading">加载中...</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getProblemDetail,
  getProblemAnswer,
  deleteProblem,
  type ProblemDetail
} from '../api/problem'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'

const route = useRoute()
const router = useRouter()

const problem = ref<ProblemDetail | null>(null)
const answer = ref<{ answer: string; explanation: string } | null>(null)
const showAnswer = ref(false)

const typeMap: Record<string, string> = {
  algorithm: '算法题',
  choice: '选择题',
  fill_blank: '填空题',
  proof: '证明题',
  research: '科研项目'
}

function typeLabel(type: string): string {
  return typeMap[type] || type
}

onMounted(async () => {
  const id = Number(route.params.id)
  if (isNaN(id)) {
    router.push('/')
    return
  }
  try {
    problem.value = await getProblemDetail(id)
  } catch (e) {
    alert('题目不存在')
    router.push('/')
  }
})

// 查看/隐藏答案
async function toggleAnswer() {
  if (!showAnswer.value && !answer.value) {
    const id = Number(route.params.id)
    try {
      answer.value = await getProblemAnswer(id)
    } catch (e) {
      alert('获取答案失败')
      return
    }
  }
  showAnswer.value = !showAnswer.value
}

// 编辑
function goEdit() {
  router.push(`/admin/problem/${route.params.id}/edit`)
}

// 删除
async function handleDelete() {
  if (!confirm('确定删除这道题吗？此操作不可撤销')) return
  try {
    await deleteProblem(Number(route.params.id))
    alert('删除成功')
    router.push('/')
  } catch (e: any) {
    alert('删除失败：' + (e.response?.data?.detail || e.message))
  }
}

// 返回列表
function goBack() {
  router.push('/')
}
</script>

<style scoped>
.problem-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 15px;
}

h2 {
  margin-top: 25px;
  margin-bottom: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #e5e7eb;
}

h3 {
  margin-top: 15px;
  margin-bottom: 8px;
}

.meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 15px;
  flex-wrap: wrap;
  color: #4b5563;
}

.tag {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.test-case {
  background: #f9fafb;
  padding: 10px;
  border-radius: 6px;
  margin: 10px 0;
}

.test-case pre {
  background: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 5px 0;
}

.option {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.subproject {
  background: #f9fafb;
  padding: 15px;
  border-radius: 8px;
  margin: 15px 0;
}

.hint {
  background: #fef3c7;
  padding: 10px;
  border-radius: 6px;
  margin-top: 10px;
}

.refs {
  margin-top: 10px;
}

.ref-item {
  margin: 5px 0;
}

.ref-note {
  color: #6b7280;
  font-size: 13px;
}

.answer-btn {
  margin-top: 20px;
  padding: 10px 20px;
  background: #16a34a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 15px;
}

.answer-btn:hover {
  background: #15803d;
}

.answer-block {
  margin-top: 15px;
  padding: 15px;
  background: #f0fdf4;
  border-radius: 8px;
  border-left: 4px solid #16a34a;
}

.actions {
  margin-top: 30px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: white;
}

.edit-btn {
  background: #2563eb;
}

.edit-btn:hover {
  background: #1d4ed8;
}

.delete-btn {
  background: #dc2626;
}

.delete-btn:hover {
  background: #b91c1c;
}

.back-btn {
  background: #6b7280;
}

.back-btn:hover {
  background: #4b5563;
}

.loading {
  text-align: center;
  padding: 50px;
  color: #9ca3af;
}
</style>