<template>
  <header class="navbar">
    <div class="navbar-content">
      <router-link to="/" class="brand">OJ Platform</router-link>

      <nav class="nav-links">
        <router-link to="/" class="nav-link">题库</router-link>
        <template v-if="userStore.isLoggedIn">
          <router-link to="/submissions" class="nav-link">我的提交</router-link>
          <router-link
            v-if="userStore.isAdmin"
            to="/admin/problem/new"
            class="nav-link"
          >
            新建题目
          </router-link>
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
          <a href="#" class="nav-link" @click.prevent="onLogout">登出</a>
        </template>

        <template v-else>
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
}

.navbar-content {
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  height: 100%;
  padding: 0 var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--color-primary);
  white-space: nowrap;
  flex-shrink: 0;
}

.nav-links {
  display: flex;
  gap: clamp(8px, 2vw, 24px);
  flex-wrap: nowrap;
  align-items: center;
  flex-shrink: 0;
}

.nav-link {
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  padding: 6px 10px;
  border-radius: var(--radius-md);
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
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
  color: white;
}

.register-btn:hover {
  background: var(--color-primary-hover);
  color: white;
}

.right-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-shrink: 0;
}

.user-area {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 4px 8px;
  border-radius: var(--radius-md);
  transition: background 0.2s;
}

.user-area:hover {
  background: rgba(0, 0, 0, 0.04);
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.username {
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  max-width: 100px;
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

@media (max-width: 768px) {
  .navbar-content {
    padding: 0 var(--spacing-md);
  }

  .nav-links {
    gap: 4px;
  }

  .nav-link {
    font-size: 13px;
    padding: 6px 6px;
  }

  .username {
    display: none;
  }
}

@media (max-width: 500px) {
  .brand {
    font-size: 16px;
  }

  .badge {
    display: none;
  }
}
</style>