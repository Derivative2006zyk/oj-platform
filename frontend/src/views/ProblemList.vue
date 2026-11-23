<template>
  <div class="problem-list">
    <!-- ===== 状态提示 ===== -->
    <div v-if="showOfflineBanner" class="offline-alert">
      离线模式：显示的是 {{ cacheAgeText }} 的缓存数据，网络恢复后自动刷新。
    </div>

    <!-- 连不上且无缓存：整页空态 -->
    <EmptyState
      v-if="blockedNoCache"
      variant="offline"
      title="无法连接到服务器"
      description="当前网络不可用，且本地没有任何缓存数据。请检查网络连接或后端地址后重试。"
      :detail="backendUrlText"
      retry-label="重新检测"
      :retrying="retrying"
      hint="提示：首次使用需要联网加载一次数据，之后断网也能查看缓存。"
      @retry="onRetry"
    >
      <template #actions>
        <button class="btn-ghost" @click="router.push('/settings')">检查后端地址</button>
      </template>
    </EmptyState>

    <!-- 连不上但有库数据缓存，只是列表空：轻量提示 -->
    <div v-else-if="connectionError && !isOffline" class="connection-alert">
      无法连接到服务器，请检查后端地址后
      <router-link to="/settings">前往设置</router-link>。
      <button class="inline-retry" :disabled="retrying" @click="onRetry">重试</button>
    </div>

    <template v-else>
      <header class="page-header">
        <h1>题库</h1>
        <p class="page-desc">共 {{ total }} 道题目</p>
      </header>

      <!-- ===== 题库导航：有数据才渲染 ===== -->
      <div v-if="bankItems.length || isAdmin" class="bank-nav">
        <button
          :class="['bank-btn', { active: selectedBank === null && !showUnassigned }]"
          @click="selectBank(null)"
        >
          全部
        </button>

        <button
          v-for="b in bankItems"
          :key="b.id"
          :class="['bank-btn', { active: selectedBank === b.id }]"
          @click="selectBank(b.id)"
        >
          {{ b.name }}
          <span v-if="typeof b.problem_count === 'number'" class="bank-count">{{ b.problem_count }}</span>
        </button>

        <button
          :class="['bank-btn', { active: showUnassigned }]"
          @click="selectUnassigned"
        >
          未归属
        </button>

        <template v-if="isAdmin">
          <button class="btn-ghost nav-action" @click="onCreateBank">+ 新建分组</button>
          <button v-if="selectedBank" class="btn-primary nav-action" @click="onCreatePaper">+ 新建试卷</button>
        </template>
      </div>

      <!-- ===== 分类导航：有数据才渲染 ===== -->
      <div v-if="categoryItems.length" class="category-nav">
        <button
          v-for="cat in categoryItems"
          :key="cat.id"
          :class="['cat-btn', { active: selectedCategory === cat.id }]"
          @click="selectCategory(cat.id)"
        >
          {{ cat.name }}
        </button>
      </div>

      <!-- ===== 筛选区 ===== -->
      <div class="card filters-card">
        <div class="filters">
          <select
            v-if="selectedBank && paperItems.length"
            v-model="selectedPaper"
            class="filter-select"
            @change="search"
          >
            <option :value="null">全部试卷</option>
            <option :value="0">仅散题</option>
            <option v-for="p in paperItems" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>

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

          <select v-if="tagItems.length" v-model="selectedTag" class="filter-select" @change="search">
            <option value="">全部标签</option>
            <option v-for="tag in tagItems" :key="tag" :value="tag">{{ tag }}</option>
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

          <template v-if="isAdmin">
            <button class="btn-ghost" @click="goCreate">录入题目</button>
            <button class="btn-ghost" @click="showOcrModal = true">拍照录题</button>
            <button class="btn-ghost" :disabled="exporting" @click="onExport">
              {{ exporting ? '导出中...' : (selectedBank !== null ? '导出该题库' : '导出全部') }}
            </button>
            <button class="btn-ghost" :disabled="importing" @click="onOpenImport">导入题库</button>
          </template>

          <button :class="['btn-ghost', { active: groupedView }]" @click="toggleGroupedView">
            {{ groupedView ? '平铺视图' : '三级分组视图' }}
          </button>
        </div>
      </div>

      <!-- ===== 平铺视图 ===== -->
      <template v-if="!groupedView">
        <EmptyState
          v-if="!loading && problemItems.length === 0"
          variant="empty"
          :title="emptyTitle"
          :description="emptyDescription"
          hint=""
        >
          <template #actions>
            <button v-if="isAdmin" class="btn-primary" @click="goCreate">录入第一道题</button>
            <button v-if="isAdmin" class="btn-ghost" @click="showOcrModal = true">拍照录题</button>
          </template>
        </EmptyState>

        <div v-else class="problem-list-body">
          <div
            v-for="problem in problemItems"
            :key="problem.id"
            class="card problem-row"
            @click="goDetail(problem.id)"
          >
            <div class="problem-id">#{{ problem.id }}</div>
            <div class="problem-main">
              <div class="problem-title">{{ problem.title || '未命名题目' }}</div>
              <div v-if="problem.tags?.length" class="problem-tags">
                <span v-for="tag in problem.tags" :key="tag" class="tag-pill">{{ tag }}</span>
              </div>
            </div>
            <div class="problem-meta">
              <span class="difficulty">{{ starText(problem.difficulty) }}</span>
              <span class="type-badge">{{ typeLabel(problem.type) }}</span>
              <span v-if="problem.paper_id" class="paper-badge">试卷 #{{ problem.paper_id }}</span>
            </div>
            <div v-if="isAdmin" class="problem-actions" @click.stop>
              <button class="btn-ghost sm" @click="goEdit(problem.id)">编辑</button>
              <button class="btn-ghost sm danger" @click="onDelete(problem.id)">删除</button>
            </div>
          </div>
        </div>

        <div v-if="total > pageSize" class="pagination">
          <button class="btn-ghost sm" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
          <span class="page-info">{{ page }} / {{ totalPages }}</span>
          <button class="btn-ghost sm" :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button>
        </div>
      </template>

      <!-- ===== 三级分组视图 ===== -->
      <template v-else>
        <div v-if="groupLoading" class="card empty-card">
          <div class="empty">正在加载分组数据...</div>
        </div>

        <EmptyState
          v-else-if="groupItems.length === 0"
          variant="empty"
          title="暂无分组数据"
          description="当前筛选条件下没有题目，或数据尚未加载。"
        />

        <div v-else class="grouped-body">
          <div v-for="bank in groupItems" :key="bank.bankKey" class="card bank-group">
            <div class="group-head" @click="toggleGroup(bank.bankKey)">
              <span class="group-arrow">{{ isOpen(bank.bankKey) ? '▾' : '▸' }}</span>
              <span class="group-title">{{ bank.bankTitle }}</span>
              <span class="group-count">{{ bank.totalCount }}</span>
            </div>

            <div v-if="isOpen(bank.bankKey)" class="group-body">
              <div v-for="paper in bank.papers" :key="paper.paperKey" class="paper-group">
                <div class="subgroup-head" @click="toggleGroup(paper.paperKey)">
                  <span class="group-arrow">{{ isOpen(paper.paperKey) ? '▾' : '▸' }}</span>
                  <span class="subgroup-title">{{ paper.paperTitle }}</span>
                  <span class="group-count">{{ paper.items.length }}</span>
                </div>

                <div v-if="isOpen(paper.paperKey)" class="subgroup-body">
                  <div
                    v-for="problem in paper.items"
                    :key="problem.id"
                    class="problem-row compact"
                    @click="goDetail(problem.id)"
                  >
                    <div class="problem-id">#{{ problem.id }}</div>
                    <div class="problem-main">
                      <div class="problem-title">{{ problem.title || '未命名题目' }}</div>
                    </div>
                    <div class="problem-meta">
                      <span class="difficulty">{{ starText(problem.difficulty) }}</span>
                      <span class="type-badge">{{ typeLabel(problem.type) }}</span>
                    </div>
                    <div v-if="isAdmin" class="problem-actions" @click.stop>
                      <button class="btn-ghost sm" @click="goEdit(problem.id)">编辑</button>
                      <button class="btn-ghost sm danger" @click="onDelete(problem.id)">删除</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </template>

    <!-- ===== 导入题库对话框 ===== -->
    <div v-if="importDialog.visible" class="modal-mask" @click.self="closeImport">
      <div class="modal">
        <header class="modal-header">
          <h2>导入题库</h2>
          <button class="modal-close" @click="closeImport">×</button>
        </header>
        <div class="modal-body">
          <input type="file" accept=".zip" @change="onPickImportFile" />
          <p v-if="importDialog.file" class="hint">已选择：{{ importDialog.file.name }}</p>

          <div class="form-item">
            <label>冲突策略</label>
            <select v-model="importDialog.strategy">
              <option value="skip">跳过同名题目</option>
              <option value="rename">重命名新题</option>
              <option value="overwrite">覆盖同名题目</option>
            </select>
          </div>

          <p v-if="importDialog.error" class="error-text">{{ importDialog.error }}</p>

          <div v-if="importDialog.result" class="import-result">
            <p>
              共 {{ importDialog.result.total }} 道，成功 {{ importDialog.result.imported }} 道，
              跳过 {{ importDialog.result.skipped }} 道，失败 {{ importDialog.result.failed }} 道
            </p>
            <ul v-if="importDialog.result.errors.length">
              <li v-for="(err, idx) in importDialog.result.errors" :key="idx">{{ err }}</li>
            </ul>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn-ghost" @click="closeImport">关闭</button>
          <button class="btn-primary" :disabled="!importDialog.file || importing" @click="onConfirmImport">
            {{ importing ? '导入中...' : '开始导入' }}
          </button>
        </footer>
      </div>
    </div>

    <OcrUploader :visible="showOcrModal" @close="showOcrModal = false" @success="onOcrSuccess" />
  </div>
</template>

<script setup lang="ts">
import EmptyState from '../components/EmptyState.vue'
import OcrUploader from '../components/OcrUploader.vue'
import { ref, reactive, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getProblems,
  getAllTags,
  getCategories,
  deleteProblem,
  type ProblemSummary,
  type Category,
} from '../api/problem'
import {
  exportBank,
  listBanks,
  importBank,
  listPapers,
  createPaper,
  createBank,
  type Bank,
  type Paper,
  type ImportResult,
} from '../api/bank'
import { useUserStore } from '../stores/user'
import { openGlobalWS, type GlobalWSHandle } from '../utils/ws'
import { setCache, getCache, getCacheEntry, hasCache } from '../utils/cache'
import { probe } from '../utils/connectivity'
import { getBackendUrl } from '../utils/backend-url'

const CACHE_KEY = 'problem_list'
const CACHE_BANKS = 'banks'
const CACHE_CATEGORIES = 'categories'
const CACHE_TAGS = 'tags'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isAdmin = computed(() => userStore.isAdmin)
// 拍照录题弹窗
const showOcrModal = ref(false)
// ===== 原始状态（不做展示，全部过滤后通过 computed 暴露） =====
const rawProblems = ref<ProblemSummary[]>([])
const rawBanks = ref<Bank[]>([])
const rawCategories = ref<Category[]>([])
const rawTags = ref<string[]>([])
const rawPapers = ref<Paper[]>([])

const loading = ref(false)
const isOffline = ref(false)
const connectionError = ref(false)
const retrying = ref(false)

const selectedBank = ref<number | null>(null)
const selectedPaper = ref<number | string | null>(null)
const showUnassigned = ref(false)
const selectedCategory = ref<number | null>(null)
const selectedTag = ref('')
const selectedType = ref('')
const difficulty = ref<number | null>(null)
const keyword = ref('')

const page = ref(1)
const pageSize = 10
const total = ref(0)

// ===== 防御性过滤：排除所有无效项 =====
const problemItems = computed(() =>
  (Array.isArray(rawProblems.value) ? rawProblems.value : []).filter(
    (p): p is ProblemSummary =>
      !!p && typeof p.id === 'number' && Number.isFinite(p.id)
  )
)

const bankItems = computed(() =>
  (Array.isArray(rawBanks.value) ? rawBanks.value : []).filter(
    (b): b is Bank =>
      !!b && typeof b.id === 'number' && Number.isFinite(b.id) &&
      typeof b.name === 'string' && b.name.trim().length > 0
  )
)

const categoryItems = computed(() =>
  (Array.isArray(rawCategories.value) ? rawCategories.value : []).filter(
    (c): c is Category =>
      !!c && typeof c.id === 'number' && Number.isFinite(c.id) &&
      typeof c.name === 'string' && c.name.trim().length > 0
  )
)

const tagItems = computed(() =>
  (Array.isArray(rawTags.value) ? rawTags.value : []).filter(
    (t): t is string => typeof t === 'string' && t.trim().length > 0
  )
)

const paperItems = computed(() =>
  (Array.isArray(rawPapers.value) ? rawPapers.value : []).filter(
    (p): p is Paper =>
      !!p && typeof p.id === 'number' && Number.isFinite(p.id) &&
      typeof p.name === 'string' && p.name.trim().length > 0
  )
)

const totalPages = computed(() => {
  if (!total.value || total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / pageSize))
})

// ===== 空态与离线 =====
const backendUrlText = computed(() => {
  const base = getBackendUrl()
  return base ? `后端地址：${base}` : '后端地址：相对路径（当前站点）'
})

const blockedNoCache = computed(() => {
  if (!isOffline.value) return false
  return !hasCache(CACHE_KEY) && problemItems.value.length === 0
})

const showOfflineBanner = computed(
  () => isOffline.value && !blockedNoCache.value && problemItems.value.length > 0
)

const cacheAgeText = computed(() => {
  const entry = getCacheEntry<{ items: ProblemSummary[]; total: number }>(CACHE_KEY)
  if (!entry?.savedAt) return '上次'
  const minutes = Math.floor((Date.now() - entry.savedAt) / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前`
  return `${Math.floor(hours / 24)} 天前`
})

const hasActiveFilter = computed(() =>
  !!keyword.value.trim() ||
  difficulty.value !== null ||
  !!selectedTag.value ||
  !!selectedType.value ||
  selectedCategory.value !== null ||
  selectedBank.value !== null ||
  showUnassigned.value
)

const emptyTitle = computed(() =>
  hasActiveFilter.value ? '没有匹配的题目' : '题库还是空的'
)

const emptyDescription = computed(() =>
  hasActiveFilter.value
    ? '试试调整搜索关键词或筛选条件。'
    : (isAdmin.value ? '录入题目或拍照识题，开始建立你的题库。' : '管理员还没有录入题目。')
)

// ===== 工具 =====
function starText(value: unknown): string {
  const n = typeof value === 'number' && Number.isFinite(value) ? Math.min(5, Math.max(0, Math.round(value))) : 0
  return n > 0 ? '★'.repeat(n) : '—'
}

function typeLabel(type: unknown): string {
  const map: Record<string, string> = {
    algorithm: '算法题',
    choice: '选择题',
    fill_blank: '填空题',
    proof: '证明题',
    research: '科研项目',
  }
  return typeof type === 'string' && map[type] ? map[type] : '题目'
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : []
}

function buildQueryParams() {
  const params: Record<string, any> = {}
  if (selectedBank.value !== null) params.bank_id = selectedBank.value
  if (showUnassigned.value) params.unassigned = true
  if (selectedPaper.value === 0) params.paper_id = 'none'
  else if (selectedPaper.value) params.paper_id = selectedPaper.value
  if (keyword.value.trim()) params.keyword = keyword.value.trim()
  if (difficulty.value) params.difficulty = difficulty.value
  if (selectedTag.value) params.tag = selectedTag.value
  if (selectedType.value) params.type = selectedType.value
  if (selectedCategory.value !== null) params.category_id = selectedCategory.value
  return params
}

function syncUrl() {
  const query: Record<string, string> = {}
  if (page.value > 1) query.page = String(page.value)
  if (keyword.value.trim()) query.keyword = keyword.value.trim()
  if (difficulty.value) query.difficulty = String(difficulty.value)
  if (selectedTag.value) query.tag = selectedTag.value
  if (selectedType.value) query.type = selectedType.value
  if (selectedCategory.value !== null) query.category_id = String(selectedCategory.value)
  if (selectedBank.value !== null) query.bank_id = String(selectedBank.value)
  if (showUnassigned.value) query.unassigned = '1'

  if (JSON.stringify(query) !== JSON.stringify(route.query)) {
    router.replace({ path: route.path, query })
  }
}

// ===== 加载 =====
async function loadProblems() {
  loading.value = true
  try {
    const data = await getProblems({ page: page.value, page_size: pageSize, ...buildQueryParams() })
    rawProblems.value = asArray<ProblemSummary>(data?.items)
    total.value = typeof data?.total === 'number' && Number.isFinite(data.total) ? data.total : rawProblems.value.length
    isOffline.value = false
    connectionError.value = false
    setCache(CACHE_KEY, { items: rawProblems.value, total: total.value })
  } catch (e) {
    console.warn('加载题目失败', e)
    isOffline.value = true
    const cached = getCache<{ items: ProblemSummary[]; total: number }>(CACHE_KEY)
    if (cached) {
      rawProblems.value = asArray<ProblemSummary>(cached.items)
      total.value = typeof cached.total === 'number' ? cached.total : rawProblems.value.length
    } else {
      rawProblems.value = []
      total.value = 0
      connectionError.value = true
    }
  } finally {
    loading.value = false
    syncUrl()
  }
}

async function loadBanks() {
  try {
    rawBanks.value = asArray<Bank>(await listBanks())
    setCache(CACHE_BANKS, rawBanks.value)
  } catch (e) {
    console.warn('加载分组失败', e)
    const cached = getCache<Bank[]>(CACHE_BANKS)
    rawBanks.value = cached ? asArray<Bank>(cached) : []
  }
}

async function loadCategoriesAndTags() {
  try {
    rawCategories.value = asArray<Category>(await getCategories())
    setCache(CACHE_CATEGORIES, rawCategories.value)
  } catch (e) {
    const cached = getCache<Category[]>(CACHE_CATEGORIES)
    rawCategories.value = cached ? asArray<Category>(cached) : []
  }

  try {
    rawTags.value = asArray<string>(await getAllTags())
    setCache(CACHE_TAGS, rawTags.value)
  } catch (e) {
    const cached = getCache<string[]>(CACHE_TAGS)
    rawTags.value = cached ? asArray<string>(cached) : []
  }
}

async function loadPapers(bankId: number | null) {
  selectedPaper.value = null
  if (!bankId) {
    rawPapers.value = []
    return
  }
  try {
    rawPapers.value = asArray<Paper>(await listPapers(bankId))
  } catch (e) {
    console.warn('加载试卷失败', e)
    rawPapers.value = []
  }
}

async function onRetry() {
  if (retrying.value) return
  retrying.value = true
  const ok = await probe()
  try {
    if (ok) {
      isOffline.value = false
      connectionError.value = false
      await Promise.all([loadProblems(), loadBanks(), loadCategoriesAndTags()])
      if (groupedView.value) await loadGrouped()
    }
  } finally {
    retrying.value = false
  }
}

// ===== 交互 =====
watch(selectedBank, (bankId) => { loadPapers(bankId) })

function search() {
  page.value = 1
  loadProblems()
  if (groupedView.value) loadGrouped()
}

function selectCategory(id: number) {
  selectedCategory.value = selectedCategory.value === id ? null : id
  search()
}

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

function changePage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadProblems()
}

function goDetail(id: number) { router.push(`/problem/${id}`) }
function goCreate() { router.push('/admin/problem/new') }
function goEdit(id: number) { router.push(`/admin/problem/${id}/edit`) }

function onOcrSuccess() {
  showOcrModal.value = false
  loadProblems()
  loadBanks()
}

async function onDelete(id: number) {
  if (!confirm(`确定删除题目 #${id} 吗？此操作不可恢复。`)) return
  try {
    await deleteProblem(id)
    await loadProblems()
    if (groupedView.value) loadGrouped()
  } catch (e: any) {
    alert('删除失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  }
}

async function onCreateBank() {
  const name = prompt('请输入新分组名称：')
  if (!name?.trim()) return
  try {
    const bank = await createBank({ name: name.trim() })
    await loadBanks()
    if (bank && typeof bank.id === 'number') selectBank(bank.id)
  } catch (e: any) {
    alert('创建失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  }
}

async function onCreatePaper() {
  if (!selectedBank.value) return
  const name = prompt('请输入新试卷名称：')
  if (!name?.trim()) return
  try {
    await createPaper({ name: name.trim(), bank_id: selectedBank.value })
    await loadPapers(selectedBank.value)
  } catch (e: any) {
    alert('创建失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  }
}

// ===== 导出与导入 =====
const exporting = ref(false)
const importing = ref(false)

const importDialog = reactive({
  visible: false,
  file: null as File | null,
  strategy: 'skip' as 'skip' | 'rename' | 'overwrite',
  error: '',
  result: null as ImportResult | null,
})

async function onExport() {
  if (exporting.value) return
  exporting.value = true
  try {
    await exportBank({ bank_id: selectedBank.value ?? null, problem_ids: null })
  } catch (e: any) {
    alert('导出失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  } finally {
    exporting.value = false
  }
}

function onOpenImport() {
  importDialog.visible = true
  importDialog.file = null
  importDialog.error = ''
  importDialog.result = null
}

function closeImport() {
  if (importing.value) return
  importDialog.visible = false
}

function onPickImportFile(e: Event) {
  const input = e.target as HTMLInputElement
  importDialog.file = input.files?.[0] || null
  importDialog.error = ''
  importDialog.result = null
}

async function onConfirmImport() {
  if (!importDialog.file || importing.value) return
  importing.value = true
  importDialog.error = ''
  try {
    importDialog.result = await importBank(importDialog.file, importDialog.strategy)
    await loadProblems()
    await loadBanks()
    if (groupedView.value) loadGrouped()
  } catch (e: any) {
    importDialog.error = e?.response?.data?.detail || e?.message || '导入失败'
  } finally {
    importing.value = false
  }
}

// ===== 三级分组视图 =====
const groupedView = ref(false)
const groupLoading = ref(false)
const groupItems = ref<Array<{
  bankKey: string
  bankTitle: string
  totalCount: number
  papers: Array<{ paperKey: string; paperTitle: string; items: ProblemSummary[] }>
}>>([])
const openGroups = ref<Record<string, boolean>>({})

function toggleGroupedView() {
  groupedView.value = !groupedView.value
  if (groupedView.value) loadGrouped()
}

function isOpen(key: string) {
  return openGroups.value[key] !== false
}

function toggleGroup(key: string) {
  openGroups.value[key] = !isOpen(key)
}

async function loadGrouped() {
  groupLoading.value = true
  try {
    const data = await getProblems({ page: 1, page_size: 200, ...buildQueryParams() })
    const items = asArray<ProblemSummary>(data?.items).filter(
      p => p && typeof p.id === 'number'
    )

    const bankIndex = new Map<number, string>()
    bankItems.value.forEach(b => bankIndex.set(b.id, b.name))

    const bankMap = new Map<number, { title: string; items: ProblemSummary[] }>()

    items.forEach(item => {
      const bankId = typeof item.bank_id === 'number' ? item.bank_id : -1
      const title = bankIndex.get(bankId) || (bankId === -1 ? '未归属' : `分组 #${bankId}`)
      if (!bankMap.has(bankId)) bankMap.set(bankId, { title, items: [] })
      bankMap.get(bankId)!.items.push(item)
    })

    groupItems.value = Array.from(bankMap.entries()).map(([bankId, bank]) => {
      const paperMap = new Map<number, { title: string; items: ProblemSummary[] }>()

      bank.items.forEach(item => {
        const paperId = typeof item.paper_id === 'number' ? item.paper_id : -1
        const title = paperId === -1 ? '散题' : `试卷 #${paperId}`
        if (!paperMap.has(paperId)) paperMap.set(paperId, { title, items: [] })
        paperMap.get(paperId)!.items.push(item)
      })

      return {
        bankKey: `bank-${bankId}`,
        bankTitle: bank.title,
        totalCount: bank.items.length,
        papers: Array.from(paperMap.entries()).map(([paperId, paper]) => ({
          paperKey: `paper-${bankId}-${paperId}`,
          paperTitle: paper.title,
          items: paper.items,
        })),
      }
    })
  } catch (e) {
    console.warn('加载分组视图失败', e)
    groupItems.value = []
  } finally {
    groupLoading.value = false
  }
}

// ===== 生命周期 =====
let globalWs: GlobalWSHandle | null = null
let onlineHandler: (() => void) | null = null
let keywordTimer: number | undefined

watch(keyword, () => {
  window.clearTimeout(keywordTimer)
  keywordTimer = window.setTimeout(() => search(), 400)
})

onMounted(async () => {
  if (route.query.bank_id) selectedBank.value = Number(route.query.bank_id)
  else if (route.query.unassigned === '1') showUnassigned.value = true
  if (route.query.keyword) keyword.value = String(route.query.keyword)
  if (route.query.difficulty) difficulty.value = Number(route.query.difficulty)
  if (route.query.tag) selectedTag.value = String(route.query.tag)
  if (route.query.type) selectedType.value = String(route.query.type)
  if (route.query.category_id) selectedCategory.value = Number(route.query.category_id)

  const cached = getCache<{ items: ProblemSummary[]; total: number }>(CACHE_KEY)
  if (cached && page.value === 1) {
    rawProblems.value = asArray<ProblemSummary>(cached.items)
    total.value = typeof cached.total === 'number' ? cached.total : rawProblems.value.length
    isOffline.value = true
  }

  await Promise.all([loadProblems(), loadBanks(), loadCategoriesAndTags()])

  globalWs = openGlobalWS((msg) => {
    if (['problem.created', 'problem.updated', 'problem.deleted'].includes(msg.type)) {
      loadProblems()
      loadBanks()
      if (groupedView.value) loadGrouped()
    }
  })

  onlineHandler = () => { onRetry() }
  window.addEventListener('online', onlineHandler)
})

onUnmounted(() => {
  if (globalWs) globalWs.close()
  if (onlineHandler) window.removeEventListener('online', onlineHandler)
  window.clearTimeout(keywordTimer)
})
</script>

<style scoped>
.problem-list {
  max-width: 960px;
  margin: 0 auto;
  padding: var(--spacing-xl) var(--spacing-lg);
  color: var(--color-text-primary);
}

.offline-alert {
  background: var(--color-sample-bg);
  color: var(--color-text-secondary);
  padding: 10px 16px;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
  font-size: 14px;
  border: 1px dashed var(--color-border);
  text-align: center;
}

.connection-alert {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  padding: 10px 16px;
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-md);
  font-size: 14px;
  border: 1px solid var(--color-warning-text);
}

.connection-alert a {
  color: var(--color-primary);
  font-weight: bold;
  text-decoration: underline;
}

.inline-retry {
  margin-left: 10px;
  padding: 2px 10px;
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: transparent;
  color: inherit;
  font-size: 12px;
  cursor: pointer;
}

.inline-retry:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-header { margin-bottom: var(--spacing-lg); }

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

.bank-nav {
  display: flex;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
  align-items: center;
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
  white-space: nowrap;
}

.bank-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.bank-btn.active { background: var(--color-primary); color: var(--color-primary-text); border-color: var(--color-primary); }

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

.nav-action { margin-left: 0; }

.bank-nav .btn-ghost.nav-action:first-of-type { margin-left: auto; }

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
  white-space: nowrap;
}

.cat-btn:hover { border-color: var(--color-primary); color: var(--color-primary); }
.cat-btn.active { background: var(--color-primary); color: var(--color-primary-text); border-color: var(--color-primary); }

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.2s;
}

.card:hover { box-shadow: var(--shadow-card-hover); }

.filters-card { padding: var(--spacing-md); margin-bottom: var(--spacing-lg); }

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
  background: var(--color-bg-page);
  color: var(--color-text-primary);
}

.search-input:focus { border-color: var(--color-primary); }

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  font-size: var(--font-size-body);
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.filter-select:focus { border-color: var(--color-primary); }

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
  white-space: nowrap;
}

.btn-primary:hover { background: var(--color-primary-hover); }
.btn-primary:disabled { background: var(--color-primary-disabled); cursor: not-allowed; }

.btn-ghost {
  padding: 8px 20px;
  background: transparent;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  white-space: nowrap;
}

.btn-ghost:hover:not(:disabled) {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.btn-ghost:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-ghost.active { background: var(--color-primary); color: var(--color-primary-text); border-color: var(--color-primary); }

.btn-ghost.sm { padding: 4px 10px; font-size: 12px; border-radius: var(--radius-sm); }
.btn-ghost.danger:hover:not(:disabled) {
  background: var(--color-danger-bg);
  border-color: var(--color-danger-text);
  color: var(--color-danger-text);
}

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

.problem-row:hover { transform: translateY(-1px); }
.problem-row.compact { padding: var(--spacing-sm) var(--spacing-md); border-radius: 0; box-shadow: none; }
.problem-row.compact:hover { transform: none; background: var(--color-primary-light); }

.problem-id {
  flex-shrink: 0;
  min-width: 44px;
  font-family: var(--font-family-mono);
  font-size: 13px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.problem-main { flex: 1; min-width: 0; }

.problem-title {
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.problem-tags { display: flex; gap: 6px; flex-wrap: wrap; }

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

.problem-actions { display: flex; gap: 6px; flex-shrink: 0; }

.paper-badge {
  padding: 2px 10px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  font-size: 12px;
  border-radius: 12px;
  white-space: nowrap;
  font-weight: 500;
}

.type-badge {
  padding: 2px 10px;
  background: var(--color-tag-bg);
  color: var(--color-tag-text);
  font-size: 12px;
  border-radius: 12px;
  white-space: nowrap;
}

.difficulty { font-size: 13px; color: var(--color-text-secondary); }

.empty-card { padding: 60px 20px; text-align: center; }
.empty { color: var(--color-text-muted); font-size: var(--font-size-body); }

.pagination {
  margin-top: var(--spacing-lg);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  flex-wrap: wrap;
}

.page-info { font-size: var(--font-size-small); color: var(--color-text-secondary); }

.grouped-body { display: flex; flex-direction: column; gap: var(--spacing-md); }
.bank-group { overflow: hidden; }

.group-head,
.subgroup-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.subgroup-head { padding: var(--spacing-sm) var(--spacing-lg); }

.group-head:hover,
.subgroup-head:hover { background: var(--color-primary-light); }

.group-arrow {
  display: inline-block;
  color: var(--color-text-muted);
  font-size: 10px;
  flex-shrink: 0;
}

.group-title { font-size: var(--font-size-body); font-weight: 600; color: var(--color-text-primary); flex: 1; }
.subgroup-title { font-size: var(--font-size-small); font-weight: 500; color: var(--color-text-secondary); flex: 1; }

.group-count {
  font-size: 12px;
  padding: 1px 8px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 10px;
  font-family: var(--font-family-mono);
}

.group-body { border-top: 1px solid var(--color-border-light); }
.subgroup-body { display: flex; flex-direction: column; border-top: 1px solid var(--color-border-light); }

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--spacing-lg);
}

.modal {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-light);
}

.modal-header h2 { margin: 0; font-size: 16px; font-weight: var(--font-weight-bold); color: var(--color-text-primary); }

.modal-close {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover { background: var(--color-primary-light); color: var(--color-primary); }
.modal-body { padding: var(--spacing-lg); overflow-y: auto; }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  border-top: 1px solid var(--color-border-light);
}

.form-item { display: flex; flex-direction: column; gap: 6px; margin-bottom: var(--spacing-md); }
.form-item label { font-size: var(--font-size-small); color: var(--color-text-secondary); font-weight: 500; }

.form-item input[type="file"],
.form-item select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  outline: none;
}

.hint { font-size: 12px; color: var(--color-text-secondary); margin: 8px 0 0; }
.error-text { margin: 8px 0 0; padding: 8px 12px; background: var(--color-danger-bg); color: var(--color-danger-text); border-radius: var(--radius-sm); font-size: 13px; }

.import-result {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--color-text-secondary);
}

.import-result ul { margin: 8px 0 0; padding-left: 18px; }
.import-result li { margin-bottom: 4px; }

@media (max-width: 600px) {
  .problem-list { padding: var(--spacing-lg) var(--spacing-md); }
  .problem-row { padding: var(--spacing-md); gap: var(--spacing-sm); flex-wrap: wrap; }
  .problem-meta { flex-direction: row; gap: 6px; }
  .problem-actions { width: 100%; justify-content: flex-end; }
  .filters { gap: var(--spacing-xs); }
  .search-input { flex: 1 1 100%; }
  .btn-primary, .btn-ghost { padding: 8px 14px; font-size: var(--font-size-small); }
  .group-head { padding: var(--spacing-md); }
  .subgroup-head { padding: var(--spacing-sm) var(--spacing-md); }
  .modal-mask { padding: var(--spacing-md); align-items: flex-end; }
  .modal { max-height: 85vh; }
  .bank-nav .btn-ghost.nav-action:first-of-type { margin-left: 0; }
}

[data-theme="dark"] .problem-title,
[data-theme="dark"] .page-header h1,
[data-theme="dark"] .group-title { color: #f8fafc !important; }

[data-theme="dark"] .page-desc,
[data-theme="dark"] .difficulty,
[data-theme="dark"] .subgroup-title { color: #94a3b8 !important; }

[data-theme="dark"] .tag-pill { background: rgba(59, 130, 246, 0.2) !important; color: #93c5fd !important; }
[data-theme="dark"] .type-badge { background: #334155 !important; color: #cbd5e1 !important; }
[data-theme="dark"] .paper-badge { background: rgba(245, 158, 11, 0.2) !important; color: #fbbf24 !important; }
[data-theme="dark"] .btn-ghost { color: #e2e8f0 !important; border-color: #334155 !important; }
[data-theme="dark"] .btn-ghost:hover:not(:disabled) { background: rgba(59, 130, 246, 0.1) !important; color: #60a5fa !important; border-color: #3b82f6 !important; }
[data-theme="dark"] .search-input,
[data-theme="dark"] .filter-select { background: #000000 !important; color: #f8fafc !important; border-color: #334155 !important; }
[data-theme="dark"] .filter-select option { background: #151515 !important; color: #f8fafc !important; }
</style>