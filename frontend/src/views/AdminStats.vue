<template>
  <main class="admin-page">
    <div class="container">
      <header class="page-header">
        <h1>全局统计</h1>
        <router-link to="/admin/users" class="btn-secondary">
          用户管理
        </router-link>
      </header>

      <div v-if="loading" class="empty-state">加载中...</div>

      <template v-else-if="stats">
        <!-- 用户统计 -->
        <section class="card stat-section">
          <div class="section-title">用户</div>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_users }}</div>
              <div class="stat-label">总用户</div>
            </div>
            <div class="stat-item">
              <div class="stat-value primary">{{ stats.total_admins }}</div>
              <div class="stat-label">管理员</div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">{{ stats.active_users }}</div>
              <div class="stat-label">正常用户</div>
            </div>
            <div class="stat-item">
              <div class="stat-value danger">{{ stats.banned_users }}</div>
              <div class="stat-label">已封禁</div>
            </div>
          </div>
        </section>

        <!-- 提交统计 -->
        <section class="card stat-section">
          <div class="section-title">提交</div>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_submissions }}</div>
              <div class="stat-label">总提交</div>
            </div>
            <div class="stat-item">
              <div class="stat-value success">{{ stats.total_accepted }}</div>
              <div class="stat-label">通过数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value primary">{{ acceptanceRate }}%</div>
              <div class="stat-label">通过率</div>
            </div>
          </div>
        </section>

        <!-- 题目统计 -->
        <section class="card stat-section">
          <div class="section-title">题库</div>
          <div class="stat-grid">
            <div class="stat-item">
              <div class="stat-value">{{ stats.total_problems }}</div>
              <div class="stat-label">题目总数</div>
            </div>
          </div>
        </section>
      </template>

      <div v-else class="empty-state">加载失败</div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAdminStats, type AdminStats } from '../api/admin'

const stats = ref<AdminStats | null>(null)
const loading = ref(true)

const acceptanceRate = computed(() => {
  if (!stats.value || stats.value.total_submissions === 0) return '0.00'
  return (
    (stats.value.total_accepted / stats.value.total_submissions) * 100
  ).toFixed(2)
})

async function load() {
  loading.value = true
  try {
    stats.value = await getAdminStats()
  } catch (e) {
    console.error('加载统计失败', e)
    stats.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.admin-page {
  padding: var(--spacing-xl) 0;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.page-header h1 {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.btn-secondary {
  padding: 8px 20px;
  background: white;
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-body);
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.btn-secondary:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--spacing-lg);
  overflow: hidden;
}

.stat-section {
  padding: var(--spacing-lg);
}

.section-title {
  font-size: var(--font-size-small);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--color-border-light);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--spacing-md);
}

.stat-item {
  padding: var(--spacing-md);
  background: var(--color-sample-bg);
  border-radius: var(--radius-md);
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
  line-height: 1.2;
}

.stat-value.primary {
  color: var(--color-primary);
}

.stat-value.success {
  color: var(--color-success-text);
}

.stat-value.danger {
  color: var(--color-danger-text);
}

.stat-label {
  margin-top: 6px;
  font-size: var(--font-size-small);
  color: var(--color-text-secondary);
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--color-text-muted);
}
</style>