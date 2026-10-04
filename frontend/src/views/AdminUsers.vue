<template>
  <main class="admin-page">
    <div class="container">
      <header class="page-header">
        <h1>用户管理</h1>
        <div class="header-actions">
          <router-link to="/admin/stats" class="btn-secondary">
            查看统计
          </router-link>
        </div>
      </header>

      <!-- 筛选栏 -->
      <section class="card filter-card">
        <div class="filter-row">
          <input
            v-model="filters.keyword"
            class="search-input"
            type="text"
            placeholder="搜索用户名或邮箱"
            @keyup.enter="onSearch"
          />

          <select v-model="filters.role" class="filter-select" @change="onSearch">
            <option value="">全部角色</option>
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>

          <select
            v-model="filters.isActive"
            class="filter-select"
            @change="onSearch"
          >
            <option value="">全部状态</option>
            <option :value="true">正常</option>
            <option :value="false">已封禁</option>
          </select>

          <button class="btn-primary" @click="onSearch">搜索</button>
          <button class="btn-secondary" @click="onReset">重置</button>
        </div>
      </section>

      <!-- 用户列表 -->
      <section class="card">
        <div v-if="loading" class="empty-state">加载中...</div>
        <div v-else-if="users.length === 0" class="empty-state">
          没有匹配的用户
        </div>

        <table v-else class="user-table">
          <thead>
            <tr>
              <th class="col-id">ID</th>
              <th>用户名</th>
              <th>邮箱</th>
              <th class="col-role">角色</th>
              <th class="col-status">状态</th>
              <th class="col-time">注册时间</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" :class="{ banned: !u.is_active }">
              <td class="col-id">{{ u.id }}</td>
              <td class="username">{{ u.username }}</td>
              <td class="email">{{ u.email }}</td>
              <td class="col-role">
                <span :class="['role-badge', `role-${u.role}`]">
                  {{ u.role === 'admin' ? '管理员' : '用户' }}
                </span>
              </td>
              <td class="col-status">
                <span :class="['status-badge', u.is_active ? 'active' : 'banned']">
                  {{ u.is_active ? '正常' : '已封禁' }}
                </span>
              </td>
              <td class="col-time">{{ formatTime(u.created_at) }}</td>
              <td class="col-actions">
                <button
                  class="action-btn"
                  :disabled="u.id === currentUserId"
                  @click="toggleRole(u)"
                >
                  {{ u.role === 'admin' ? '降为用户' : '升为管理员' }}
                </button>
                <button
                  :class="['action-btn', u.is_active ? 'danger' : 'success']"
                  :disabled="u.id === currentUserId"
                  @click="toggleStatus(u)"
                >
                  {{ u.is_active ? '封禁' : '解封' }}
                </button>
              </td>
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
import { ref, reactive, computed, onMounted } from 'vue'
import {
  listUsers,
  changeUserRole,
  changeUserStatus,
  type AdminUser,
} from '../api/admin'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const currentUserId = computed(() => userStore.user?.id)

const users = ref<AdminUser[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20

const filters = reactive({
  keyword: '',
  role: '',
  isActive: '' as '' | boolean,
})

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function formatTime(s: string): string {
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  } catch {
    return s
  }
}

async function load() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.role) params.role = filters.role
    if (filters.isActive !== '') params.is_active = filters.isActive

    const data = await listUsers(params)
    users.value = data.items
    total.value = data.total
  } catch (e) {
    console.error('加载用户失败', e)
    users.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  load()
}

function onReset() {
  filters.keyword = ''
  filters.role = ''
  filters.isActive = ''
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

async function toggleRole(u: AdminUser) {
  const newRole = u.role === 'admin' ? 'user' : 'admin'
  const action = newRole === 'admin' ? '升为管理员' : '降为普通用户'
  if (!confirm(`确定将 ${u.username} ${action}？`)) return

  try {
    const updated = await changeUserRole(u.id, newRole)
    Object.assign(u, updated)
  } catch (e: any) {
    alert(e?.response?.data?.detail || '操作失败')
  }
}

async function toggleStatus(u: AdminUser) {
  const newStatus = !u.is_active
  const action = newStatus ? '解封' : '封禁'
  if (!confirm(`确定${action}用户 ${u.username}？`)) return

  try {
    const updated = await changeUserStatus(u.id, newStatus)
    Object.assign(u, updated)
  } catch (e: any) {
    alert(e?.response?.data?.detail || '操作失败')
  }
}

onMounted(load)
</script>

<style scoped>
.admin-page {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

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

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
}

.filter-card {
  padding: var(--spacing-md);
}

.filter-row {
  display: flex;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 200px;
  padding: 8px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  outline: none;
}

.search-input:focus {
  border-color: var(--color-primary);
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  background: var(--color-bg-card);
  cursor: pointer;
  outline: none;
}

.btn-primary,
.btn-secondary {
  padding: 8px 20px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
  border: none;
  text-decoration: none;
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-primary-text);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: white;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
}

.user-table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td {
  padding: 12px var(--spacing-md);
  text-align: left;
  font-size: var(--font-size-body);
  border-bottom: 1px solid var(--color-border-light);
}

.user-table tbody tr:hover {
  background: rgba(0, 0, 0, 0.015);
}

.user-table tbody tr.banned {
  opacity: 0.6;
}

.user-table th {
  background: var(--color-editor-header-bg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-secondary);
  font-size: var(--font-size-small);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.col-id { width: 60px; }
.col-role { width: 100px; }
.col-status { width: 90px; }
.col-time { width: 130px; }
.col-actions { width: 200px; }

.username {
  font-weight: 500;
}

.email {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.role-badge,
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-admin { background: var(--color-warning-bg); color: var(--color-warning-text); }
.role-user { background: var(--color-neutral-bg); color: var(--color-neutral-text); }

.status-badge.active { background: var(--color-success-bg); color: var(--color-success-text); }
.status-badge.banned { background: var(--color-danger-bg); color: var(--color-danger-text); }

.action-btn {
  padding: 4px 10px;
  margin-right: 6px;
  background: white;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.action-btn.danger:hover:not(:disabled) {
  border-color: var(--color-danger-text);
  color: var(--color-danger-text);
}

.action-btn.success:hover:not(:disabled) {
  border-color: var(--color-success-text);
  color: var(--color-success-text);
}

.action-btn:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

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

@media (max-width: 900px) {
  .col-time, .col-id {
    display: none;
  }
  .col-actions {
    width: auto;
  }
}

@media (max-width: 600px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>