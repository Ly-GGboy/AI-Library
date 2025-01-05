<template>
  <div class="doc-tree" :class="{ 'nav-hidden': isNavHidden }">
    <!-- 移动端导航按钮 -->
    <MobileNav
      v-if="isMobile"
      :is-hidden="isNavHidden"
      @toggle="toggleNav"
    />

    <!-- 主内容区域 -->
    <div class="nav-content" :class="{ 'hidden': isNavHidden && isMobile }">
      <!-- 搜索框 -->
      <div class="search-box">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索文章..."
          class="search-input"
        />
      </div>

      <!-- 最近访问 -->
      <div v-if="recentArticles.length > 0" class="recent-articles">
        <div class="section-title">最近访问</div>
        <div v-for="article in recentArticles" :key="article.path" class="recent-article">
          <router-link
            :to="{ name: 'doc', params: { path: article.path } }"
            class="recent-article-link"
            :class="{ 'active': isCurrentArticle(article.path) }"
          >
            <DocumentTextIcon class="w-4 h-4" :class="isCurrentArticle(article.path) ? 'text-primary-500' : 'text-gray-500'" />
            <span class="article-name">{{ article.name }}</span>
          </router-link>
        </div>
      </div>

      <!-- 文档树 -->
      <div v-if="loading" class="loading">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="docTree" class="tree-container" ref="treeContainer">
        <TreeNode :node="docTree" :filter="searchQuery" />
      </div>
      <div v-else class="empty">
        暂无文档
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useDocStore } from '../stores/doc'
import TreeNode from './TreeNode.vue'
import MobileNav from './MobileNav.vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const docStore = useDocStore()
const { docTree, loading, error } = storeToRefs(docStore)
const searchQuery = ref('')
const treeContainer = ref<HTMLElement | null>(null)
const isNavHidden = ref(false)

// 检测是否为移动设备
const isMobile = computed(() => {
  return window.innerWidth < 768
})

// 切换导航显示
const toggleNav = () => {
  isNavHidden.value = !isNavHidden.value
}

// 监听窗口大小变化
onMounted(() => {
  window.addEventListener('resize', () => {
    if (!isMobile.value) {
      isNavHidden.value = false
    }
  })
})

// 最近访问的文章
const RECENT_ARTICLES_KEY = 'recent-articles'
const MAX_RECENT_ARTICLES = 5
const recentArticles = ref<Array<{path: string, name: string}>>([])

// 从 localStorage 加载最近访问的文章
const loadRecentArticles = () => {
  const saved = localStorage.getItem(RECENT_ARTICLES_KEY)
  if (saved) {
    recentArticles.value = JSON.parse(saved)
  }
}

// 添加文章到最近访问
const addToRecentArticles = (path: string) => {
  if (!path) return
  
  // 从文档树中查找文章名称
  const findArticleName = (node: any, path: string): string | null => {
    if (node.path === path) return node.name.replace('.md', '')
    if (node.children) {
      for (const child of node.children) {
        const found = findArticleName(child, path)
        if (found) return found
      }
    }
    return null
  }

  const name = findArticleName(docTree.value, path)
  if (!name) return

  const article = { path, name }
  recentArticles.value = [
    article,
    ...recentArticles.value.filter(a => a.path !== path)
  ].slice(0, MAX_RECENT_ARTICLES)
  
  localStorage.setItem(RECENT_ARTICLES_KEY, JSON.stringify(recentArticles.value))
}

// 检查是否是当前文章
const isCurrentArticle = (path: string) => {
  return route.params.path === path
}

// 监听文档树加载
watch(docTree, (newDocTree) => {
  if (newDocTree && route.params.path) {
    addToRecentArticles(route.params.path as string)
  }
})

// 监听路由变化
watch(
  () => route.params.path,
  (newPath) => {
    if (typeof newPath === 'string' && docTree.value) {
      addToRecentArticles(newPath)
      if (isMobile.value) {
        isNavHidden.value = true
      }
    }
  },
  { immediate: true }
)

onMounted(async () => {
  if (!docTree.value) {
    await docStore.loadDocTree()
  }
  loadRecentArticles()
  
  // 如果有最后访问的文章，滚动到其位置
  const lastVisited = recentArticles.value[0]?.path
  if (lastVisited && treeContainer.value) {
    // 等待树渲染完成
    setTimeout(() => {
      const element = treeContainer.value?.querySelector(`[href*="${lastVisited}"]`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 500)
  }
})
</script>

<style scoped>
.doc-tree {
  @apply h-full relative flex flex-col;
}

.nav-content {
  @apply flex-1 flex flex-col transition-all duration-300 ease-in-out;
}

/* 移动端样式 */
@media (max-width: 767px) {
  .doc-tree {
    @apply fixed inset-0 z-30 bg-white dark:bg-gray-900;
  }

  .nav-content {
    @apply absolute inset-0 pt-16;
  }

  .nav-content.hidden {
    @apply -translate-x-full opacity-0;
  }

  .search-box {
    @apply sticky top-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm z-10;
  }
}

.search-box {
  @apply p-4 border-b dark:border-gray-700;
}

.search-input {
  @apply w-full px-3 py-2 rounded-lg border border-gray-300 
    focus:border-primary-500 focus:ring-1 focus:ring-primary-500
    dark:bg-gray-800 dark:border-gray-600 
    dark:text-gray-200 dark:placeholder-gray-400
    dark:focus:border-primary-400 dark:focus:ring-primary-400;
}

.recent-articles {
  @apply p-4 border-b dark:border-gray-700;
}

.section-title {
  @apply text-sm font-medium text-gray-500 mb-2 dark:text-gray-400;
}

.recent-article {
  @apply mb-1;
}

.recent-article-link {
  @apply flex items-center gap-2 px-2 py-1 rounded 
    hover:bg-gray-100 transition-colors duration-200
    dark:hover:bg-gray-800;
}

.recent-article-link.active {
  @apply bg-primary-50 hover:bg-primary-100
    dark:bg-primary-900/30 dark:hover:bg-primary-900/40;
}

.article-name {
  @apply text-sm text-gray-700 truncate dark:text-gray-300;
}

.tree-container {
  @apply flex-1 overflow-y-auto p-4;
}

.loading {
  @apply flex justify-center items-center py-8;
}

.error {
  @apply text-red-500 p-4 rounded bg-red-50 my-4
    dark:text-red-400 dark:bg-red-900/20;
}

.empty {
  @apply text-gray-500 text-center py-8 dark:text-gray-400;
}
</style> 