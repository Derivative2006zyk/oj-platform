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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('oj_token')

  // 需要登录的页面
  if (to.meta.requiresAuth && !token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  // 仅游客能进的页面（已登录则跳首页）
  if (to.meta.guestOnly && token) {
    next('/')
    return
  }

  next()
})

export default router