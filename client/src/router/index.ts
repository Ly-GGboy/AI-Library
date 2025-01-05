import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DocView from '../views/DocView.vue'
import SearchView from '../views/SearchView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/doc/:path(.*)',
      name: 'doc',
      component: DocView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    }
  ]
})

export default router 