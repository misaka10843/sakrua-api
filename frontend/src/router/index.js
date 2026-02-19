import {createRouter, createWebHistory} from 'vue-router'
import Contributors from '../pages/Contributors.vue'

const routes = [
    {
        path: '/',
        redirect: '/contributors'
    },
    {
        path: '/contributors',
        name: 'Contributors',
        component: Contributors,
        meta: {title: 'Contributors config', icon: 'mdi-account-group'}
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router