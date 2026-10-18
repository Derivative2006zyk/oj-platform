<template>
  <header class="navbar">
    <div class="navbar-content">
      <router-link to="/" class="brand">OJ</router-link>

      <nav class="nav-links">
        <router-link to="/" class="nav-link">题库</router-link>
        <template v-if="userStore.isLoggedIn">
          <router-link to="/submissions" class="nav-link">我的提交</router-link>
          <template v-if="userStore.isAdmin">
            <router-link to="/admin/users" class="nav-link">用户管理</router-link>
            <router-link to="/admin/stats" class="nav-link">统计</router-link>
          </template>
        </template>
      </nav>

      <div class="right-section">
        <template v-if="userStore.isLoggedIn">
          <router-link to="/profile" class="user-area">
            <div class="avatar">
              {{ (userStore.user?.username || '?').slice(0, 1).toUpperCase() }}
            </div>
            <span class="username">{{ userStore.user?.username }}</span>
            <span v-if="userStore.isAdmin" class="badge">管理员</span>
          </router-link>
          <router-link to="/settings" class="nav-link">设置</router-link>
          <a href="#" class="nav-link logout-btn" @click.prevent="onLogout">登出</a>
        </template>

        <template v-else>
          <router-link to="/settings" class="nav-link">设置</router-link>
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link register-btn">注册</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

function onLogout() {
  userStore.logout()
  router.push('/')
}
</script>

<style scoped>
.navbar {
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--color-nav-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: var(--shadow-nav);
  border-bottom: 1px solid var(--color-border-light);
  width: 100%;
}

.navbar-content {
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
  padding: 0 var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  /* 防止内部元素撑开父级 */
  min-width: 0;
}

.brand {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
  flex-shrink: 0;
}

/* 导航链接区 */
.nav-links {
  display: flex;
  gap: clamp(8px, 2vw, 24px);
  flex-wrap: nowrap;
  align-items: center;
  /* 允许横向滚动 */
  overflow-x: auto;
  scrollbar-width: none;
  flex-shrink: 1;
  min-width: 0;
}

.nav-links::-webkit-scrollbar {
  display: none;
}

.nav-link {
  font-size: 14px;
  color: var(--color-text-secondary);
  padding: 6px 8px;
  border-radius: var(--radius-md);
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  flex-shrink: 0;
}

.nav-link:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-primary);
}

.nav-link.router-link-active {
  color: var(--color-primary);
  font-weight: 500;
}

.register-btn {
  background: var(--color-primary);
  color: var(--color-primary-text);
}

.right-section {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: var(--radius-md);
  transition: background 0.2s;
  flex-shrink: 0;
}

.user-area:hover {
  background: rgba(0, 0, 0, 0.04);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.username {
  font-size: 14px;
  color: var(--color-text-primary);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  padding: 2px 6px;
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
  font-size: 11px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.logout-btn {
  color: var(--color-danger-text);
}

/* ===== 移动端深度适配 ===== */
@media (max-width: 768px) {
  .brand {
    font-size: 16px;
  }
  
  .username,
  .badge {
    display: none; /* 手机上隐藏用户名和徽章，只留头像 */
  }

  .nav-link {
    font-size: 13px;
    padding: 6px;
  }
}
</style>