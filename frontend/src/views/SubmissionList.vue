<template>
  <main class="submission-page">
    <div class="container">
      <!-- 页面标题栏 -->
      <header class="page-header">
        <h1>我的提交</h1>
        <div class="filter-area">
          <label>状态</label>
          <select v-model="filterStatus" class="status-select" @change="onFilterChange">
            <option value="">全部</option>
            <option value="PENDING">排队中</option>
            <option value="AC">通过</option>
            <option value="WA">答案错误</option>
            <option value="TLE">时间超限</option>
            <option value="MLE">内存超限</option>
            <option value="RE">运行错误</option>
            <option value="CE">编译错误</option>
          </select>
        </div>
      </header>

      <!-- 列表卡片 -->
      <section class="card">
        <div v-if="loading" class="empty-state">加载中...</div>
        <div v-else-if="items.length === 0" class="empty-state">
          暂无提交记录
        </div>

        <table v-else class="submission-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th>题目</th>
              <th class="col-lang">语言</th>
              <th class="col-status">状态</th>
              <th class="col-cases">测试点</th>
              <th class="col-runtime">耗时</th>
              <th class="col-time">提交时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td class="col-id">
                <span class="id-text">#{{ item.id }}</span>
              </td>
              <td>
                <router-link :to="`/problem/${item.problem_id}`" class="problem-link">
                  题目 #{{ item.problem_id }}
                </router-link>
              </td>
              <td class="col-lang">
                <span class="lang-badge">{{ item.language }}</span>
              </td>
              <td class="col-status">
                <span :class="['status-badge', `status-${item.status}`]">
                  {{ statusLabel(item.status) }}
                </span>
              </td>
              <td class="col-cases">
                {{ item.passed_cases }} / {{ item.total_cases }}
              </td>
              <td class="col-runtime">
                {{ item.runtime_ms != null ? item.runtime_ms + ' ms' : '-' }}
              </td>
              <td class="col-time">{{ formatTime(item.created_at) }}</td>
            </tr>
          </tbody>
        </table>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination">
          <button
            class="page-btn"
            :disabled="page <= 1"
            @click="prevPage"
          >
            上一页
          </button>
          <span class="page-info">
            第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条
          </span>
          <button
            class="page-btn"
            :disabled="page >= totalPages"
            @click="nextPage"
          >
            下一页
          </button>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listMySubmissions } from '../api/submission'

interface SubmissionItem {
  id: number
  problem_id: number
  language: string
  status: string
  passed_cases: number
  total_cases: number
  runtime_ms: number | null
  created_at: string
}

const loading = ref(true)
const items = ref<SubmissionItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterStatus = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

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

function formatTime(s: string): string {
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return s
  }
}

async function load() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filterStatus.value) params.status = filterStatus.value

    const data = await listMySubmissions(params)
    items.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('加载失败', e)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  page.value = 1
  load()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    load()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    load()
  }
}

onMounted(load)
</script>

<style scoped>
.submission-page {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

/* ===== 页面标题栏 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.page-header h1 {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.filter-area {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-body);
}

.filter-area label {
  color: var(--color-text-secondary);
}

.status-select {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  background: var(--color-bg-card);
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s;
}

.status-select:focus {
  border-color: var(--color-primary);
}

/* ===== 列表卡片 ===== */
.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.card:hover {
  box-shadow: var(--shadow-card-hover);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
  font-size: var(--font-size-body);
}

/* ===== 表格 ===== */
.submission-table {
  width: 100%;
  border-collapse: collapse;
}

.submission-table th,
.submission-table td {
  padding: 12px var(--spacing-md);
  text-align: left;
  font-size: var(--font-size-body);
  border-bottom: 1px solid var(--color-border-light);
}

.submission-table tbody tr:last-child td {
  border-bottom: none;
}

.submission-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.015);
}

.submission-table th {
  background: var(--color-editor-header-bg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.col-id { width: 80px; }
.col-lang { width: 100px; }
.col-status { width: 110px; }
.col-cases { width: 90px; }
.col-runtime { width: 100px; }
.col-time { width: 160px; }

.id-text {
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
  font-size: 13px;
}

.problem-link {
  color: var(--color-primary);
  font-weight: 500;
  transition: color 0.2s;
}

.problem-link:hover {
  color: var(--color-primary-hover);
  text-decoration: underline;
}

.lang-badge {
  display: inline-block;
  padding: 2px 10px;
  background: var(--color-tag-bg);
  color: var(--color-tag-text);
  font-size: 12px;
  font-family: var(--font-family-mono);
  border-radius: 12px;
  font-weight: 500;
}

/* ===== 状态徽章 ===== */
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 500;
  font-size: 12px;
}

.status-PENDING { background: var(--color-neutral-bg); color: var(--color-neutral-text); }
.status-AC { background: var(--color-success-bg); color: var(--color-success-text); }
.status-WA { background: var(--color-danger-bg); color: var(--color-danger-text); }
.status-TLE { background: var(--color-warning-bg); color: var(--color-warning-text); }
.status-MLE { background: var(--color-warning-bg); color: var(--color-warning-text); }
.status-RE { background: var(--color-danger-bg); color: var(--color-danger-text); }
.status-CE { background: var(--color-danger-bg); color: var(--color-danger-text); }

/* ===== 分页 ===== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-top: 1px solid var(--color-border-light);
  font-size: var(--font-size-body);
}

.page-btn {
  padding: 6px 16px;
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-secondary);
}

/* ===== 响应式 ===== */
@media (max-width: 900px) {
  .col-cases, .col-runtime, .col-time {
    display: none;
  }
}

@media (max-width: 600px) {
  .container {
    padding: 0 var(--spacing-md);
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .col-lang {
    display: none;
  }
}
</style>