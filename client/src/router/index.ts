import { createRouter, createWebHistory } from 'vue-router'

// 使用动态导入实现路由懒加载
const HomeView = () => import('../views/HomeView.vue')
const DocView = () => import('../views/DocView.vue')
const SearchView = () => import('../views/SearchView.vue')
const AdminDashboard = () => import('../views/AdminDashboard.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: {
        title: 'AI Library - 首页'
      }
    },
    {
      path: '/doc/:path(.*)',
      name: 'doc',
      component: DocView,
      meta: {
        title: 'AI Library - 文档阅读'
      }
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView,
      meta: {
        title: 'AI Library - 搜索结果'
      }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: AdminDashboard,
      meta: {
        title: '管理后台 - AI Library'
      }
    }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth'
      }
    } else {
      return { top: 0 }
    }
  }
})

// 动态设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title as string || 'AI Library'
  next()
})

export default router 