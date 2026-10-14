<template>
  <div class="problem-list">
    <header class="page-header">
      <h1>题库</h1>
      <p class="page-desc">共 {{ total }} 道题目</p>
    </header>

    <!-- 题库导航 -->
    <div class="bank-nav">
      <button
        :class="['bank-btn', { active: selectedBank === null && !showUnassigned }]"
        @click="selectBank(null)"
      >
        全部
      </button>
      <button
        v-for="b in banks"
        :key="b.id"
        :class="['bank-btn', { active: selectedBank === b.id }]"
        @click="selectBank(b.id)"
      >
        {{ b.name }}
        <span class="bank-count">{{ b.problem_count }}</span>
      </button>
      <button
        :class="['bank-btn', { active: showUnassigned }]"
        @click="selectUnassigned"
      >
        未归属
      </button>
    </div>

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
        <button
          class="btn-ghost"
          :disabled="exporting"
          @click="onExportAll"
        >
          {{ exporting ? '导出中...' : '导出题库' }}
        </button>
        <button
          :class="['btn-ghost', { active: groupedView }]"
          @click="toggleGroupedView"
        >
          {{ groupedView ? '平铺视图' : '分组视图' }}
        </button>
      </div>
    </div>

    <!-- 平铺视图 -->
    <template v-if="!groupedView">
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
    </template>

    <!-- 分组视图 -->
    <template v-else>
      <div v-if="groupLoading" class="card empty-card">
        <div class="empty">加载中...</div>
      </div>

      <div v-else-if="groupedProblems.length === 0" class="card empty-card">
        <div class="empty">暂无题目</div>
      </div>

      <div v-else class="group-list">
        <div
          v-for="group in groupedProblems"
          :key="group.key"
          class="card group-card"
        >
          <div
            class="group-header"
            @click="toggleGroup(group.key)"
          >
            <span class="group-arrow" :class="{ open: isGroupOpen(group.key) }">
              ▶
            </span>
            <span class="group-title">{{ group.title }}</span>
            <span class="group-count">{{ group.items.length }}</span>
          </div>

          <div v-show="isGroupOpen(group.key)" class="group-body">
            <div
              v-for="problem in group.items"
              :key="problem.id"
              class="problem-row group-row"
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
        </div>
      </div>
    </template>
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
import { exportBank, listBanks, type Bank } from '../api/bank'

const router = useRouter()
const route = useRoute()

// ===== 状态 =====
const problems = ref<ProblemSummary[]>([])
const categories = ref<Category[]>([])
const allTags = ref<string[]>([])
const banks = ref<Bank[]>([])

// 题库筛选
const selectedBank = ref<number | null>(null)
const showUnassigned = ref(false)

// 分页
const page = ref(Number(route.query.page) || 1)
const pageSize = 10
const total = ref(0)

// 筛选条件
const keyword = ref((route.query.keyword as string) || '')
const difficulty = ref<number | null>(
  route.query.difficulty ? Number(route.query.difficulty) : null
)
const selectedTag = ref((route.query.tag as string) || '')
const selectedType = ref((route.query.type as string) || '')
const selectedCategory = ref<number | null>(
  route.query.category_id ? Number(route.query.category_id) : null
)

// 导出
const exporting = ref(false)

// 分组视图
const groupedView = ref(false)
const groupLoading = ref(false)
const groupedProblems = ref<{ key: string; title: string; items: ProblemSummary[] }[]>([])
const openGroups = ref<Record<string, boolean>>({})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

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
  if (selectedBank.value !== null) query.bank_id = String(selectedBank.value)
  if (showUnassigned.value) query.unassigned = '1'

  router.replace({ query })
}

// ===== 基础筛选参数 =====
function buildQueryParams() {
  const params: any = {
    category_id: selectedCategory.value || undefined,
    difficulty: difficulty.value || undefined,
    type: selectedType.value || undefined,
    tag: selectedTag.value || undefined,
    keyword: keyword.value || undefined,
  }
  if (selectedBank.value !== null) {
    params.bank_id = selectedBank.value
  } else if (showUnassigned.value) {
    params.unassigned = true
  }
  return params
}

// ===== 加载题目列表 =====
async function loadProblems() {
  try {
    const data = await getProblems({
      page: page.value,
      page_size: pageSize,
      ...buildQueryParams(),
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

// ===== 搜索 =====
function search() {
  page.value = 1
  loadProblems()
  if (groupedView.value) {
    loadGrouped()
  }
}

// ===== 选择分类 =====
function selectCategory(id: number) {
  selectedCategory.value = selectedCategory.value === id ? null : id
  search()
}

// ===== 选择题库 =====
function selectBank(id: number | null) {
  selectedBank.value = id
  showUnassigned.value = false
  search()
}

function selectUnassigned() {
  selectedBank.value = null
  showUnassigned.value = true
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

// ===== 导出 =====
async function onExportAll() {
  if (exporting.value) return
  exporting.value = true
  try {
    const ids: number[] | null = selectedBank.value !== null
      ? null  // 全量或按需扩展
      : null
    await exportBank({ problem_ids: ids })
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 401 || status === 403) {
      alert('需要管理员密钥，请先在题目编辑页填写后重试')
    } else {
      alert(e?.response?.data?.detail || '导出失败')
    }
  } finally {
    exporting.value = false
  }
}

// ===== 分组视图 =====
async function toggleGroupedView() {
  groupedView.value = !groupedView.value
  if (groupedView.value) {
    await loadGrouped()
  }
}

async function loadGrouped() {
  groupLoading.value = true
  try {
    // 一次拉取全部匹配题目
    const data = await getProblems({
      page: 1,
      page_size: 200,
      ...buildQueryParams(),
    })
    const items: ProblemSummary[] = Array.isArray(data?.items) ? data.items : []

    // 按 bank_id 分组
    const map = new Map<string, { key: string; title: string; items: ProblemSummary[] }>()
    const banksById = new Map(banks.value.map(b => [b.id, b]))

    for (const p of items) {
      const bid = (p as any).bank_id
      const key = bid == null ? '__unassigned__' : String(bid)
      if (!map.has(key)) {
        const bank = bid != null ? banksById.get(bid) : null
        map.set(key, {
          key,
          title: bank ? bank.name : '未归属题库',
          items: [],
        })
      }
      map.get(key)!.items.push(p)
    }

    // 排序：已归属题库按 sort_order，未归属放最后
    const groups = Array.from(map.values())
    groups.sort((a, b) => {
      if (a.key === '__unassigned__') return 1
      if (b.key === '__unassigned__') return -1
      const ba = banksById.get(Number(a.key))
      const bb = banksById.get(Number(b.key))
      const sa = ba ? ba.sort_order : 0
      const sb = bb ? bb.sort_order : 0
      return sa - sb
    })

    groupedProblems.value = groups

    // 默认全部展开
    const nextOpen: Record<string, boolean> = { ...openGroups.value }
    for (const g of groups) {
      if (nextOpen[g.key] === undefined) nextOpen[g.key] = true
    }
    openGroups.value = nextOpen
  } catch (e) {
    console.error('加载分组视图失败', e)
    groupedProblems.value = []
  } finally {
    groupLoading.value = false
  }
}

function toggleGroup(key: string) {
  openGroups.value = { ...openGroups.value, [key]: !openGroups.value[key] }
}

function isGroupOpen(key: string): boolean {
  return openGroups.value[key] !== false
}

// ===== 加载题库列表 =====
async function loadBanks() {
  try {
    const data = await listBanks()
    banks.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('加载题库失败', e)
    banks.value = []
  }
}

// ===== 防抖搜索 =====
let searchTimer: number | null = null
watch(keyword, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    search()
  }, 500)
})

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

// ===== 初始化 =====
onMounted(async () => {
  // 从 URL 恢复题库筛选
  if (route.query.bank_id) {
    selectedBank.value = Number(route.query.bank_id)
  } else if (route.query.unassigned === '1') {
    showUnassigned.value = true
  }

  try {
    const [cats, tags, bs] = await Promise.all([
      getCategories(),
      getAllTags(),
      listBanks(),
    ])
    categories.value = Array.isArray(cats) ? cats : []
    allTags.value = Array.isArray(tags) ? tags : []
    banks.value = Array.isArray(bs) ? bs : []
  } catch (e) {
    console.error('加载分类/标签/题库失败', e)
    categories.value = []
    allTags.value = []
    banks.value = []
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

/* ===== 题库导航 ===== */
.bank-nav {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.bank-btn {
  padding: 6px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  cursor: pointer;
  font-size: var(--font-size-small);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.bank-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.bank-btn.active {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-color: var(--color-primary);
}

.bank-count {
  font-size: 11px;
  padding: 0 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
  font-family: var(--font-family-mono);
}

.bank-btn:not(.active) .bank-count {
  background: var(--color-primary-light);
  color: var(--color-primary);
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

/* ===== 卡片 ===== */
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-card-hover);
}

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

.btn-ghost.active {
  background: var(--color-primary);
  color: var(--color-primary-text);
  border-color: var(--color-primary);
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

/* ===== 分组视图 ===== */
.group-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.group-card {
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid transparent;
  transition: background 0.15s;
}

.group-header:hover {
  background: var(--color-primary-light);
}

.group-arrow {
  display: inline-block;
  color: var(--color-text-muted);
  font-size: 10px;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.group-arrow.open {
  transform: rotate(90deg);
}

.group-title {
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.group-count {
  font-size: 12px;
  padding: 1px 8px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 10px;
  font-family: var(--font-family-mono);
}

.group-body {
  border-top: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
}

.group-row {
  border-radius: 0;
  box-shadow: none;
  border-bottom: 1px solid var(--color-border-light);
}

.group-row:last-child {
  border-bottom: none;
}

.group-row:hover {
  transform: none;
  background: var(--color-primary-light);
  box-shadow: none;
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

  .group-header {
    padding: var(--spacing-md);
  }
}
</style>