<template>
  <div class="problem-list">
    <header class="page-header">
      <h1>题库</h1>
      <p class="page-desc">共 {{ total }} 道题目</p>
    </header>

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
    <div class="card filters-card">
      <div class="filters">
        <input
          v-model="keyword"
          class="search-input"
          placeholder="搜索题目..."
          @keyup.enter="search"
        />
        <select v-model="difficulty" class="filter-select" @change="search">
          <option :value="null">全部难度</option>
          <option v-for="d in 5" :key="d" :value="d">{{ '★'.repeat(d) }}</option>
        </select>
        <select v-model="selectedTag" class="filter-select" @change="search">
          <option value="">全部标签</option>
          <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
        </select>
        <select v-model="selectedType" class="filter-select" @change="search">
          <option value="">全部题型</option>
          <option value="algorithm">算法题</option>
          <option value="choice">选择题</option>
          <option value="fill_blank">填空题</option>
          <option value="proof">证明题</option>
          <option value="research">科研项目</option>
        </select>
        <button class="btn-primary" @click="search">搜索</button>
        <button class="btn-ghost" @click="goCreate">录入题目</button>
      </div>
    </div>

    <!-- 题目列表 -->
    <div v-if="problems.length === 0" class="card empty-card">
      <div class="empty">暂无题目</div>
    </div>

    <div v-else class="problem-list-body">
      <div
        v-for="problem in problems"
        :key="problem.id"
        class="card problem-row"
        @click="goDetail(problem.id)"
      >
        <div class="problem-id">#{{ problem.id }}</div>
        <div class="problem-main">
          <div class="problem-title">{{ problem.title }}</div>
          <div v-if="problem.tags && problem.tags.length" class="problem-tags">
            <span v-for="tag in problem.tags" :key="tag" class="tag-pill">{{ tag }}</span>
          </div>
        </div>
        <div class="problem-meta">
          <span class="type-badge">{{ typeLabel(problem.type) }}</span>
          <span class="difficulty">{{ '★'.repeat(problem.difficulty) }}</span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="total > 0">
      <button class="btn-ghost" :disabled="page <= 1" @click="changePage(page - 1)">
        上一页
      </button>
      <span class="page-info">
        第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条
      </span>
      <button class="btn-ghost" :disabled="page >= totalPages" @click="changePage(page + 1)">
        下一页
      </button>
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
  try {
    const data = await getProblems({
      page: page.value,
      page_size: pageSize,
      category_id: selectedCategory.value || undefined,
      difficulty: difficulty.value || undefined,
      type: selectedType.value || undefined,
      tag: selectedTag.value || undefined,
      keyword: keyword.value || undefined
    })
    problems.value = Array.isArray(data?.items) ? data.items : []
    total.value = typeof data?.total === 'number' ? data.total : 0
  } catch (e) {
    console.error('加载题目列表失败', e)
    problems.value = []
    total.value = 0
  }
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
  try {
    const [cats, tags] = await Promise.all([getCategories(), getAllTags()])
    categories.value = Array.isArray(cats) ? cats : []
    allTags.value = Array.isArray(tags) ? tags : []
  } catch (e) {
    console.error('加载分类/标签失败', e)
    categories.value = []
    allTags.value = []
  }
  await loadProblems()
})
</script>

<style scoped>
.problem-list {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
}

/* ===== 页头 ===== */
.page-header {
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-xs);
}

.page-desc {
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  margin: 0;
}

/* ===== 分类导航 ===== */
.category-nav {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
}

.cat-btn {
  padding: 6px 18px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: var(--font-size-small);
  transition: all 0.2s;
}

.cat-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.cat-btn.active {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-color: var(--color-primary);
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

/* ===== 筛选卡片 ===== */
.filters-card {
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.filters {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1 1 200px;
  min-width: 150px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  outline: none;
  transition: border-color 0.2s;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
}

.search-input:focus {
  border-color: var(--color-primary);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  font-size: var(--font-size-body);
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.filter-select:focus {
  border-color: var(--color-primary);
}

/* ===== 按钮 ===== */
.btn-primary {
  padding: 8px 20px;
  background: var(--color-primary);
  color: var(--color-primary-text);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-ghost {
  padding: 8px 20px;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  cursor: pointer;
  transition: background 0.2s;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--color-primary-light);
}

.btn-ghost:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  color: var(--color-text-muted);
  border-color: var(--color-border);
}

/* ===== 题目列表 ===== */
.problem-list-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.problem-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  transition: box-shadow 0.15s, transform 0.15s;
}

.problem-row:hover {
  transform: translateY(-1px);
}

.problem-id {
  flex-shrink: 0;
  min-width: 44px;
  font-family: var(--font-family-mono);
  font-size: 13px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.problem-main {
  flex: 1;
  min-width: 0;
}

.problem-title {
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.problem-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag-pill {
  padding: 1px 8px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 11px;
  border-radius: 10px;
}

.problem-meta {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.type-badge {
  padding: 2px 10px;
  background: var(--color-tag-bg);
  color: var(--color-tag-text);
  font-size: 12px;
  border-radius: 12px;
  white-space: nowrap;
}

.difficulty {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* ===== 空状态 ===== */
.empty-card {
  padding: 60px 20px;
  text-align: center;
}

.empty {
  color: var(--color-text-muted);
  font-size: var(--font-size-body);
}

/* ===== 分页 ===== */
.pagination {
  margin-top: var(--spacing-lg);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.page-info {
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

/* ===== 响应式 ===== */
@media (max-width: 600px) {
  .problem-list {
    padding: var(--spacing-lg) var(--spacing-md);
  }

  .problem-row {
    padding: var(--spacing-md);
    gap: var(--spacing-sm);
  }

  .problem-meta {
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  .filters {
    gap: var(--spacing-xs);
  }

  .search-input {
    flex: 1 1 100%;
  }

  .btn-primary,
  .btn-ghost {
    padding: 8px 14px;
    font-size: var(--font-size-small);
  }
}
</style>