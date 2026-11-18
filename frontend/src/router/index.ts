import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'problem-list',
    component: () => import('../views/ProblemList.vue'),
  },
  {
    path: '/problem/:id',
    name: 'problem-detail',
    component: () => import('../views/ProblemDetail.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/Settings.vue'),
  },
  {
    path: '/admin/problem/new',
    name: 'problem-create',
    component: () => import('../views/ProblemEdit.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/problem/:id/edit',
    name: 'problem-edit',
    component: () => import('../views/ProblemEdit.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/submissions',
    name: 'submission-list',
    component: () => import('../views/SubmissionList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../views/AdminUsers.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/stats',
    name: 'admin-stats',
    component: () => import('../views/AdminStats.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/plugin/:name',
    name: 'plugin-view',
    component: () => import('../views/PluginView.vue'),
  },
  {
    path: '/ai-test',
    name: 'AITest',
    component: () => import('../views/AITest.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(), // 【核心修复】改用 Hash 模式，兼容移动端
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('oj_token')
  const userRaw = localStorage.getItem('oj_user')

  let isAdmin = false
  if (userRaw) {
    try {
      const u = JSON.parse(userRaw)
      isAdmin = u?.role === 'admin'
    } catch {
      isAdmin = false
    }
  }

  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresAdmin && !isAdmin) {
    next('/')
    return
  }

  if (to.meta.guestOnly && token) {
    next('/')
    return
  }

  next()
})

export default router