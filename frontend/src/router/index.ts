import { createRouter, createWebHistory } from 'vue-router'
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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
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

  // 需要登录
  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 需要管理员
  if (to.meta.requiresAdmin && !isAdmin) {
    next('/')
    return
  }

  // 仅游客
  if (to.meta.guestOnly && token) {
    next('/')
    return
  }

  next()
})

export default router