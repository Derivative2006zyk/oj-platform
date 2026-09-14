<template>
  <div class="problem-edit">
    <h1>{{ isEdit ? '编辑题目' : '录入题目' }}</h1>

    <div class="form-group">
      <label>管理员密钥</label>
      <input v-model="adminKey" type="password" placeholder="用于验证录入权限" />
      <small class="hint">默认 admin-key-change-me，保存到本地浏览器</small>
    </div>

    <div class="form-group">
      <label>标题</label>
      <input v-model="form.title" placeholder="请输入题目标题" />
    </div>

    <div class="form-group">
      <label>主分类</label>
      <select v-model.number="form.category_id">
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">
          {{ cat.name }}
        </option>
      </select>
    </div>

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

    <div class="form-group">
      <label>难度</label>
      <select v-model.number="form.difficulty">
        <option v-for="d in 5" :key="d" :value="d">{{ d }}星</option>
      </select>
    </div>

    <div class="form-group">
      <label>标签（用逗号分隔）</label>
      <input v-model="tagsInput" placeholder="例如：数组,哈希表" />
    </div>

    <div class="form-group">
      <label>题目描述（Markdown 格式）</label>
      <textarea v-model="form.description" rows="8" placeholder="支持 Markdown 语法"></textarea>
    </div>

    <!-- 图片上传：非选择题、非填空题显示 -->
    <div v-if="form.type !== 'choice' && form.type !== 'fill_blank'" class="form-group">
      <label>图片上传</label>
      <input type="file" accept="image/png,image/jpeg,image/webp" @change="handleImageUpload" />
      <small class="hint">支持 PNG/JPEG/WebP，单张不超过 5MB。上传后自动插入 Markdown 图片语法到描述末尾。</small>
      <p v-if="uploadingImage" class="uploading">上传中...</p>
    </div>

    <!-- 算法题：测试用例 -->
    <div v-if="form.type === 'algorithm'" class="dynamic-block">
      <h3>测试用例</h3>
      <div v-for="(tc, idx) in form.test_cases" :key="idx" class="dynamic-item">
        <span class="item-index">#{{ idx + 1 }}</span>
        <textarea v-model="tc.input_data" rows="2" placeholder="输入数据"></textarea>
        <textarea v-model="tc.expected_output" rows="2" placeholder="期望输出"></textarea>
        <label class="checkbox-label">
          <input type="checkbox" v-model="tc.is_example" /> 作为示例展示
        </label>
        <button type="button" @click="removeTestCase(Number(idx))" class="btn-danger">删除</button>
      </div>
      <button type="button" @click="addTestCase" class="btn-success">+ 添加测试用例</button>
    </div>

    <!-- 选择题：选项 -->
    <div v-if="form.type === 'choice'" class="dynamic-block">
      <h3>选项（勾选正确答案）</h3>
      <div v-for="(opt, idx) in form.options" :key="idx" class="dynamic-item">
        <span class="item-index">{{ opt.key }}.</span>
        <input v-model="opt.content" placeholder="选项内容" />
        <label class="checkbox-label">
          <input
            type="radio"
            name="correct_option"
            :checked="opt.is_correct"
            @change="setCorrectOption(Number(idx))"
          />
          正确答案
        </label>
        <button type="button" @click="removeOption(Number(idx))" class="btn-danger">删除</button>
      </div>
      <button type="button" @click="addOption" class="btn-success">+ 添加选项</button>
    </div>

    <!-- 填空题：空位 -->
    <div v-if="form.type === 'fill_blank'" class="dynamic-block">
      <h3>填空标准答案</h3>
      <div v-for="(blank, idx) in form.blanks" :key="idx" class="dynamic-item">
        <span class="item-index">第 {{ idx + 1 }} 空</span>
        <input
          v-model="blank.answers_text"
          placeholder="标准答案，多个用 | 分隔，例如：3|三次"
        />
        <button type="button" @click="removeBlank(Number(idx))" class="btn-danger">删除</button>
      </div>
      <button type="button" @click="addBlank" class="btn-success">+ 添加填空</button>
    </div>

    <!-- 科研项目：子项目 -->
    <div v-if="form.type === 'research'" class="dynamic-block">
      <h3>子项目列表</h3>
      <div v-for="(sp, idx) in form.subprojects" :key="idx" class="subproject-edit">
        <h4>子项目 {{ idx + 1 }}</h4>
        <input v-model="sp.title" placeholder="子项目标题" />
        <textarea v-model="sp.description" rows="3" placeholder="子项目描述"></textarea>
        <input v-model="sp.hint" placeholder="思路提示（可选）" />

        <!-- 参考资源 -->
        <div v-for="(link, refIdx) in sp.reference_links" :key="refIdx" class="ref-edit">
          <input v-model="link.title" placeholder="资源标题" />
          <input v-model="link.url" placeholder="URL" />
          <input v-model="link.note" placeholder="备注（可选）" />
          <button
            type="button"
            @click="removeReferenceLink(Number(idx), Number(refIdx))"
            class="btn-danger"
          >
            删除
          </button>
        </div>
        <button type="button" @click="addReferenceLink(Number(idx))" class="btn-success">
          + 添加参考资源
        </button>

        <textarea v-model="sp.answer_guide" rows="3" placeholder="参考思路展示（可选）"></textarea>
        <button type="button" @click="removeSubproject(Number(idx))" class="btn-danger">
          删除此子项目
        </button>
      </div>
      <button type="button" @click="addSubproject" class="btn-success">+ 添加子项目</button>
    </div>

    <div class="form-group">
      <label>答案（Markdown 格式）</label>
      <textarea v-model="form.answer" rows="5" placeholder="可包含代码块"></textarea>
    </div>

    <div class="form-group">
      <label>解析（Markdown 格式）</label>
      <textarea v-model="form.explanation" rows="4" placeholder="可选"></textarea>
    </div>

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
  uploadImage,
  type Category
} from '../api/problem'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.params.id !== undefined && route.params.id !== '')

const adminKey = ref(localStorage.getItem('admin_key') || 'admin-key-change-me')
const categories = ref<Category[]>([])
const tagsInput = ref('')
const submitting = ref(false)
const uploadingImage = ref(false)

const form = reactive({
  title: '',
  category_id: 1,
  type: 'algorithm',
  difficulty: 1,
  description: '',
  answer: '',
  explanation: '',
  test_cases: [] as any[],
  options: [] as any[],
  blanks: [] as any[],
  subprojects: [] as any[]
})

// ===================== 测试用例 =====================
function addTestCase() {
  form.test_cases.push({ input_data: '', expected_output: '', is_example: true })
}
function removeTestCase(idx: number) {
  form.test_cases.splice(idx, 1)
}

// ===================== 选项 =====================
function addOption() {
  const key = String.fromCharCode(65 + form.options.length)
  form.options.push({ key, content: '', is_correct: false })
}
function removeOption(idx: number) {
  form.options.splice(idx, 1)
  form.options.forEach((opt, i) => {
    opt.key = String.fromCharCode(65 + i)
  })
}
function setCorrectOption(idx: number) {
  form.options.forEach((opt, i) => {
    opt.is_correct = i === idx
  })
}

// ===================== 填空 =====================
function addBlank() {
  form.blanks.push({ answers_text: '' })
}
function removeBlank(idx: number) {
  form.blanks.splice(idx, 1)
}

// ===================== 子项目 =====================
function addSubproject() {
  form.subprojects.push({
    title: '',
    description: '',
    hint: '',
    reference_links: [],
    answer_guide: '',
    sort_order: form.subprojects.length + 1
  })
}
function removeSubproject(idx: number) {
  form.subprojects.splice(idx, 1)
}
function addReferenceLink(spIdx: number) {
  form.subprojects[spIdx].reference_links.push({ title: '', url: '', note: '' })
}
function removeReferenceLink(spIdx: number, refIdx: number) {
  form.subprojects[spIdx].reference_links.splice(refIdx, 1)
}

// ===================== 图片上传 =====================
async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  const file = input.files[0]
  uploadingImage.value = true
  try {
    const problemId = isEdit.value ? Number(route.params.id) : undefined
    const result = await uploadImage(file, problemId)
    form.description += `\n\n![图片](${result.url})\n\n`
    alert('图片已上传，Markdown 语法已插入描述末尾')
  } catch (e: any) {
    const msg = e.response?.data?.detail || e.message || '上传失败'
    alert('上传失败：' + msg)
  } finally {
    uploadingImage.value = false
    input.value = ''
  }
}

// ===================== 组装提交数据 =====================
function buildSubmitData() {
  const base: any = {
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
      .filter(t => t)
  }

  if (form.type === 'algorithm') {
    base.test_cases = form.test_cases.map(tc => ({
      input_data: tc.input_data,
      expected_output: tc.expected_output,
      is_example: tc.is_example !== false
    }))
    base.options = null
    base.blanks = null
    base.subprojects = []
  } else if (form.type === 'choice') {
    base.test_cases = []
    base.options = form.options.map(o => ({
      key: o.key,
      content: o.content,
      is_correct: !!o.is_correct
    }))
    base.blanks = null
    base.subprojects = []
  } else if (form.type === 'fill_blank') {
    base.test_cases = []
    base.options = null
    base.blanks = form.blanks.map((b, idx) => ({
      blank_index: idx + 1,
      correct_answers: String(b.answers_text || '')
        .split('|')
        .map((s: string) => s.trim())
        .filter((s: string) => s),
      match_rule: 'exact'
    }))
    base.subprojects = []
  } else if (form.type === 'research') {
    base.test_cases = []
    base.options = null
    base.blanks = null
    base.subprojects = form.subprojects.map((sp, idx) => ({
      title: sp.title,
      description: sp.description,
      hint: sp.hint || null,
      reference_links: (sp.reference_links || []).filter((r: any) => r.title && r.url),
      answer_guide: sp.answer_guide || null,
      sort_order: idx + 1
    }))
  } else {
    base.test_cases = []
    base.options = null
    base.blanks = null
    base.subprojects = []
  }

  return base
}

// ===================== 保存 =====================
async function submit() {
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
  if (form.type === 'choice') {
    if (!Array.isArray(form.options) || form.options.length < 2) {
      alert('选择题至少需要 2 个选项')
      return
    }
    if (!form.options.some(o => o.is_correct)) {
      alert('请勾选一个正确答案')
      return
    }
  }

  localStorage.setItem('admin_key', adminKey.value)

  const data = buildSubmitData()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateProblem(Number(route.params.id), data)
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

function cancel() {
  router.push('/')
}

// ===================== 初始化 =====================
onMounted(async () => {
  try {
    categories.value = await getCategories()
  } catch (e) {
    alert('无法连接到服务器，请确认后端已启动')
    return
  }

  if (!isEdit.value) return

  const id = Number(route.params.id)
  if (isNaN(id)) {
    alert('无效的题目 ID')
    router.push('/')
    return
  }

  try {
    const detail = await getProblemDetail(id)
    form.title = detail.title || ''
    form.category_id = detail.category_id || 1
    form.type = detail.type || 'algorithm'
    form.difficulty = detail.difficulty || 1
    form.description = detail.description || ''
    form.explanation = detail.explanation || ''
    tagsInput.value = Array.isArray(detail.tags) ? detail.tags.join(',') : ''

    if (detail.type === 'algorithm') {
      form.test_cases = Array.isArray(detail.test_cases)
        ? detail.test_cases.map(tc => ({
            input_data: tc.input_data || '',
            expected_output: tc.expected_output || '',
            is_example: true
          }))
        : []
    } else if (detail.type === 'choice') {
      form.options = Array.isArray(detail.options)
        ? detail.options.map((o: any) => ({
            key: o.key || '',
            content: o.content || '',
            is_correct: !!o.is_correct
          }))
        : []
    } else if (detail.type === 'fill_blank') {
      form.blanks = Array.isArray(detail.blanks)
        ? detail.blanks.map((b: any) => ({
            answers_text: Array.isArray(b.correct_answers)
              ? b.correct_answers.join('|')
              : ''
          }))
        : []
    } else if (detail.type === 'research') {
      form.subprojects = Array.isArray(detail.subprojects)
        ? detail.subprojects.map((sp: any) => ({
            title: sp.title || '',
            description: sp.description || '',
            hint: sp.hint || '',
            reference_links: Array.isArray(sp.reference_links)
              ? sp.reference_links.map((r: any) => ({
                  title: r.title || '',
                  url: r.url || '',
                  note: r.note || ''
                }))
              : [],
            answer_guide: sp.answer_guide || '',
            sort_order: sp.sort_order || 0
          }))
        : []
    }

    try {
      const answerData = await getProblemAnswer(id)
      form.answer = answerData.answer || ''
      if (answerData.explanation) {
        form.explanation = answerData.explanation
      }
    } catch (e) {
      console.warn('获取答案失败', e)
    }
  } catch (e) {
    alert('题目不存在')
    router.push('/')
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
  margin: 15px 0 10px;
  color: #374151;
}

h4 {
  margin: 10px 0;
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

.form-group textarea {
  resize: vertical;
  font-family: 'Consolas', 'Monaco', monospace;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: #2563eb;
}

.hint {
  display: block;
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

.uploading {
  margin-top: 5px;
  color: #2563eb;
  font-size: 13px;
}

.dynamic-block {
  margin: 20px 0;
  padding: 15px;
  background: #f9fafb;
  border-radius: 8px;
}

.dynamic-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.dynamic-item textarea,
.dynamic-item input {
  flex: 1;
  min-width: 150px;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  box-sizing: border-box;
}

.item-index {
  min-width: 40px;
  padding-top: 8px;
  color: #6b7280;
  font-weight: bold;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-top: 8px;
  white-space: nowrap;
  font-size: 13px;
  cursor: pointer;
}

.subproject-edit {
  background: white;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
}

.subproject-edit > input,
.subproject-edit > textarea {
  width: 100%;
  margin-bottom: 8px;
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.ref-edit {
  display: flex;
  gap: 5px;
  margin-bottom: 5px;
}

.ref-edit input {
  flex: 1;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.btn-success,
.btn-danger {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: white;
}

.btn-success {
  background: #16a34a;
}

.btn-success:hover {
  background: #15803d;
}

.btn-danger {
  background: #dc2626;
}

.btn-danger:hover {
  background: #b91c1c;
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