import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/stock/:id',
    name: 'StockDetail',
    component: () => import('../views/StockDetailView.vue'),
    props: true,
  },
  {
    path: '/trades',
    name: 'TradeLog',
    component: () => import('../views/TradeLogView.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
