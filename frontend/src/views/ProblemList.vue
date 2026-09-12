<template>
  <div class="problem-list">
    <h1>题库</h1>

    <!-- 主分类导航 -->
    <div class="category-nav">
      <button
        v-for="cat in categories"
        :key="cat.id"
        :class="['cat-btn', { active: selectedCategory === cat.id }]"
        @click="selectCategory(cat.id)"
      >
        {{ cat.name }}
      </button>
    </div>

    <!-- 筛选区域 -->
    <div class="filters">
      <input
        v-model="keyword"
        placeholder="搜索题目..."
        @keyup.enter="search"
      />
      <select v-model="difficulty" @change="search">
        <option :value="null">全部难度</option>
        <option v-for="d in 5" :key="d" :value="d">{{ d }}星</option>
      </select>
      <select v-model="selectedTag" @change="search">
        <option value="">全部标签</option>
        <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
      </select>
      <select v-model="selectedType" @change="search">
        <option value="">全部题型</option>
        <option value="algorithm">算法题</option>
        <option value="choice">选择题</option>
        <option value="fill_blank">填空题</option>
        <option value="proof">证明题</option>
        <option value="research">科研项目</option>
      </select>
      <button @click="search">搜索</button>
      <button @click="goCreate" class="create-btn">录入题目</button>
    </div>

    <!-- 题目表格 -->
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>标题</th>
          <th>题型</th>
          <th>难度</th>
          <th>标签</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="problem in problems"
          :key="problem.id"
          @click="goDetail(problem.id)"
        >
          <td>{{ problem.id }}</td>
          <td>{{ problem.title }}</td>
          <td>{{ typeLabel(problem.type) }}</td>
          <td>{{ '★'.repeat(problem.difficulty) }}</td>
          <td>
            <span v-for="tag in problem.tags" :key="tag" class="tag">{{ tag }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="problems.length === 0" class="empty">暂无题目</p>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <button :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
      <span>
        共 {{ total }} 条 · 显示第
        {{ (page - 1) * pageSize + 1 }} -
        {{ Math.min(page * pageSize, total) }} 条 · 第 {{ page }} / {{ totalPages }} 页
      </span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getProblems,
  getAllTags,
  getCategories,
  type ProblemSummary,
  type Category
} from '../api/problem'

const router = useRouter()
const route = useRoute()

// ===== 状态 =====
const problems = ref<ProblemSummary[]>([])
const categories = ref<Category[]>([])
const allTags = ref<string[]>([])

// 分页（从 URL 初始化）
const page = ref(Number(route.query.page) || 1)
const pageSize = 10
const total = ref(0)

// 筛选条件（从 URL 初始化）
const keyword = ref((route.query.keyword as string) || '')
const difficulty = ref<number | null>(
  route.query.difficulty ? Number(route.query.difficulty) : null
)
const selectedTag = ref((route.query.tag as string) || '')
const selectedType = ref((route.query.type as string) || '')
const selectedCategory = ref<number | null>(
  route.query.category_id ? Number(route.query.category_id) : null
)

// 计算总页数
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

// 题型标签映射
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

// ===== URL 同步 =====
function syncUrl() {
  const query: Record<string, string> = {}
  if (page.value > 1) query.page = String(page.value)
  if (keyword.value) query.keyword = keyword.value
  if (difficulty.value) query.difficulty = String(difficulty.value)
  if (selectedTag.value) query.tag = selectedTag.value
  if (selectedType.value) query.type = selectedType.value
  if (selectedCategory.value) query.category_id = String(selectedCategory.value)

  router.replace({ query })
}

// ===== 加载题目列表 =====
async function loadProblems() {
  const data = await getProblems({
    page: page.value,
    page_size: pageSize,
    category_id: selectedCategory.value || undefined,
    difficulty: difficulty.value || undefined,
    type: selectedType.value || undefined,
    tag: selectedTag.value || undefined,
    keyword: keyword.value || undefined
  })
  problems.value = data.items
  total.value = data.total
  syncUrl()
}

// ===== 搜索（重置到第 1 页） =====
function search() {
  page.value = 1
  loadProblems()
}

// ===== 选择分类 =====
function selectCategory(id: number) {
  selectedCategory.value = selectedCategory.value === id ? null : id
  search()
}

// ===== 翻页 =====
function changePage(p: number) {
  page.value = p
  loadProblems()
}

// ===== 跳转 =====
function goDetail(id: number) {
  router.push(`/problem/${id}`)
}

function goCreate() {
  router.push('/admin/problem/new')
}

// ===== 防抖搜索 =====
let searchTimer: number | null = null
watch(keyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    search()
  }, 500)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

// ===== 初始化 =====
onMounted(async () => {
  const [cats, tags] = await Promise.all([getCategories(), getAllTags()])
  categories.value = cats
  allTags.value = tags
  await loadProblems()
})
</script>

<style scoped>
.problem-list {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

.category-nav {
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.cat-btn:hover {
  border-color: #2563eb;
  color: #2563eb;
}

.cat-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.filters {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters input {
  flex: 1;
  min-width: 150px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.filters select,
.filters button {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.filters button:hover {
  background: #f3f4f6;
}

.create-btn {
  background: #16a34a !important;
  color: white;
  border-color: #16a34a !important;
}

.create-btn:hover {
  background: #15803d !important;
}

.tag {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 10px;
  margin-right: 5px;
  font-size: 12px;
  display: inline-block;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background: #f9fafb;
  font-weight: 600;
}

tbody tr {
  cursor: pointer;
  transition: background 0.15s;
}

tbody tr:hover {
  background: #f9fafb;
}

.empty {
  text-align: center;
  color: #9ca3af;
  margin-top: 30px;
  padding: 40px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination button:not(:disabled):hover {
  background: #f3f4f6;
}
</style>