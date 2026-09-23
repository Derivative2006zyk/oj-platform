<template>
  <nav class="navbar">
    <div class="nav-left">
      <router-link to="/" class="brand">OJ Platform</router-link>
    </div>

    <div class="nav-right">
      <template v-if="userStore.isLoggedIn">
        <span class="username">
          {{ userStore.user?.username }}
          <span v-if="userStore.isAdmin" class="badge">管理员</span>
        </span>
        <router-link
          v-if="userStore.isAdmin"
          to="/admin/problem/new"
          class="nav-link"
        >
          新建题目
        </router-link>
        <a href="#" class="nav-link" @click.prevent="onLogout">登出</a>
      </template>

      <template v-else>
        <router-link to="/login" class="nav-link">登录</router-link>
        <router-link to="/register" class="nav-link">注册</router-link>
      </template>
    </div>
  </nav>
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
  height: 60px;
  padding: 0 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-sizing: border-box;
}

.brand {
  font-size: 18px;
  font-weight: 600;
  color: #4f46e5;
  text-decoration: none;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.nav-link {
  color: #374151;
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
}

.nav-link:hover {
  color: #4f46e5;
}

.username {
  font-size: 14px;
  color: #374151;
}

.badge {
  margin-left: 6px;
  padding: 2px 6px;
  background: #fef3c7;
  color: #92400e;
  font-size: 12px;
  border-radius: 3px;
}
</style>