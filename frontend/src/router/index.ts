import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'problem-list',
            component: () => import('../views/ProblemList.vue')
        },
        {
            path: '/problem/:id',
            name: 'problem-detail',
            component: () => import('../views/ProblemDetail.vue')
        },
        {
            path: '/admin/problem/new',
            name: 'problem-create',
            component: () => import('../views/ProblemEdit.vue')
        },
        {
            path: '/admin/problem/:id/edit',
            name: 'problem-edit',
            component: () => import('../views/ProblemEdit.vue')
        }
    ]
})

export default router