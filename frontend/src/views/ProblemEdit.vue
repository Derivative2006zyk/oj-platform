<template>
  <div class="problem-edit">
    <h1>{{ isEdit ? '编辑题目' : '录入题目' }}</h1>

    <!-- 管理员密钥 -->
    <div class="form-group">
      <label>管理员密钥</label>
      <input
        v-model="adminKey"
        type="password"
        placeholder="用于验证录入权限"
      />
      <small class="hint">默认 admin-key-change-me，保存到本地浏览器</small>
    </div>

    <!-- 标题 -->
    <div class="form-group">
      <label>标题</label>
      <input v-model="form.title" placeholder="请输入题目标题" />
    </div>

    <!-- 主分类 -->
    <div class="form-group">
      <label>主分类</label>
      <select v-model="form.category_id">
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">
          {{ cat.name }}
        </option>
      </select>
    </div>

    <!-- 题型（编辑时禁止切换） -->
    <div class="form-group">
      <label>题型</label>
      <select v-model="form.type" :disabled="isEdit">
        <option value="algorithm">算法题</option>
        <option value="choice">选择题</option>
        <option value="fill_blank">填空题</option>
        <option value="proof">证明题</option>
        <option value="research">科研项目</option>
      </select>
      <small v-if="isEdit" class="hint">编辑时不能修改题型</small>
    </div>

    <!-- 难度 -->
    <div class="form-group">
      <label>难度</label>
      <select v-model="form.difficulty">
        <option v-for="d in 5" :key="d" :value="d">{{ d }}星</option>
      </select>
    </div>

    <!-- 标签 -->
    <div class="form-group">
      <label>标签（用逗号分隔）</label>
      <input v-model="tagsInput" placeholder="例如：数组,哈希表" />
    </div>

    <!-- 题目描述 -->
    <div class="form-group">
      <label>题目描述（Markdown 格式）</label>
      <textarea
        v-model="form.description"
        rows="8"
        placeholder="支持 Markdown 语法"
      ></textarea>
    </div>

    <!-- 题型专属表单占位 -->
    <div class="dynamic-area">
      <h3>题型专属内容</h3>
      <p class="placeholder">（第12天实现）</p>
    </div>

    <!-- 答案与解析 -->
    <div class="form-group">
      <label>答案（Markdown 格式）</label>
      <textarea
        v-model="form.answer"
        rows="5"
        placeholder="可包含代码块"
      ></textarea>
    </div>

    <div class="form-group">
      <label>解析（Markdown 格式）</label>
      <textarea
        v-model="form.explanation"
        rows="4"
        placeholder="可选"
      ></textarea>
    </div>

    <!-- 操作按钮 -->
    <div class="actions">
      <button @click="submit" :disabled="submitting" class="submit-btn">
        {{ submitting ? '保存中...' : '保存' }}
      </button>
      <button @click="cancel" class="cancel-btn">取消</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCategories,
  getProblemDetail,
  getProblemAnswer,
  createProblem,
  updateProblem,
  type Category
} from '../api/problem'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.params.id !== undefined)

// 管理员密钥
const adminKey = ref(localStorage.getItem('admin_key') || 'admin-key-change-me')

// 分类列表
const categories = ref<Category[]>([])

// 标签输入（逗号分隔的字符串）
const tagsInput = ref('')

// 提交状态
const submitting = ref(false)

// 表单数据
const form = reactive({
  title: '',
  category_id: 1,
  type: 'algorithm',
  difficulty: 1,
  description: '',
  answer: '',
  explanation: '',
  // 以下字段在第12天使用
  test_cases: [] as any[],
  options: [] as any[],
  blanks: [] as any[],
  subprojects: [] as any[]
})

// 保存表单
async function submit() {
  // 基础校验
  if (!form.title.trim()) {
    alert('请填写标题')
    return
  }
  if (!form.description.trim()) {
    alert('请填写题目描述')
    return
  }
  if (!adminKey.value.trim()) {
    alert('请填写管理员密钥')
    return
  }

  // 保存密钥到本地
  localStorage.setItem('admin_key', adminKey.value)

  // 组装请求数据
  const data: any = {
    title: form.title.trim(),
    category_id: form.category_id,
    type: form.type,
    difficulty: form.difficulty,
    description: form.description,
    answer: form.answer || null,
    explanation: form.explanation || null,
    tags: tagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t),
    // 以下字段在第12天完善
    test_cases: [],
    options: null,
    blanks: null,
    subprojects: []
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      const id = Number(route.params.id)
      await updateProblem(id, data)
      alert('更新成功')
    } else {
      await createProblem(data)
      alert('创建成功')
    }
    router.push('/')
  } catch (e: any) {
    const msg = e.response?.data?.detail || e.message || '保存失败'
    alert('保存失败：' + msg)
  } finally {
    submitting.value = false
  }
}

// 取消
function cancel() {
  router.push('/')
}

// 初始化
onMounted(async () => {
  // 加载分类
  categories.value = await getCategories()

  // 编辑模式：回填数据
  if (isEdit.value) {
    const id = Number(route.params.id)
    try {
      const detail = await getProblemDetail(id)
      form.title = detail.title
      form.category_id = detail.category_id
      form.type = detail.type
      form.difficulty = detail.difficulty
      form.description = detail.description
      form.explanation = detail.explanation || ''
      tagsInput.value = detail.tags.join(',')

      // 答案通过单独接口获取
      try {
        const answerData = await getProblemAnswer(id)
        form.answer = answerData.answer || ''
        // 解析已在 detail 中返回，但以 answer 接口为准
        if (answerData.explanation) {
          form.explanation = answerData.explanation
        }
      } catch (e) {
        console.warn('获取答案失败', e)
      }

      // 以下字段在第12天回填
      // form.test_cases = detail.test_cases
      // form.options = detail.options || []
      // form.blanks = detail.blanks || []
      // form.subprojects = detail.subprojects
    } catch (e) {
      alert('题目不存在')
      router.push('/')
    }
  }
})
</script>

<style scoped>
.problem-edit {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

h3 {
  margin-bottom: 10px;
  color: #374151;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #374151;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
}

.form-group textarea {
  resize: vertical;
  font-family: 'Consolas', 'Monaco', monospace;
}

.hint {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

.dynamic-area {
  margin: 20px 0;
  padding: 15px;
  background: #f9fafb;
  border-radius: 8px;
}

.placeholder {
  color: #9ca3af;
  font-size: 14px;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.submit-btn {
  padding: 12px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.submit-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 12px 24px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
}

.cancel-btn:hover {
  background: #4b5563;
}
</style>