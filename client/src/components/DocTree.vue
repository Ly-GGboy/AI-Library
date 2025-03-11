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
      <!-- 文档树 -->
      <div v-if="loading" class="loading">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      <div v-else-if="docTree" class="tree-container" ref="treeContainer">
        <h3 class="section-title">文件夹</h3>
        <TreeNode :node="docTree" :filter="filter" />
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
import { DocumentTextIcon, ChevronDoubleDownIcon, ChevronDoubleUpIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  loadData: {
    type: Boolean,
    default: true
  },
  filter: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const docStore = useDocStore()
const { docTree, loading, error } = storeToRefs(docStore)
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
const MAX_RECENT_ARTICLES = 6
const recentArticles = ref<Array<{path: string, name: string}>>([])

// 从 localStorage 加载最近访问的文章
const loadRecentArticles = () => {
  const saved = localStorage.getItem(RECENT_ARTICLES_KEY)
  if (saved) {
    try {
      recentArticles.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to parse recent articles:', e)
      recentArticles.value = []
    }
  }
}

// 添加文章到最近访问
const addToRecentArticles = (path: string) => {
  if (!path) return
  
  // 从文档树中查找文章名称
  const findArticleName = (node: any, path: string): string | null => {
    if (node.path === path) {
      // 移除 .md 或 .pdf 后缀
      return node.name.replace(/\.(md|pdf)$/, '')
    }
    if (node.children) {
      for (const child of node.children) {
        const found = findArticleName(child, path)
        if (found) return found
      }
    }
    return null
  }

  const name = findArticleName(docTree.value, path)
  console.log('Found article name:', name, 'for path:', path)
  if (!name) return

  const article = { path, name }
  console.log('Current recent articles before update:', recentArticles.value)
  
  // 移除已存在的相同文章（如果有）
  const existingIndex = recentArticles.value.findIndex(a => a.path === path)
  if (existingIndex !== -1) {
    recentArticles.value.splice(existingIndex, 1)
  }
  
  // 在开头添加新文章
  recentArticles.value.unshift(article)
  
  // 如果超过6条记录，只保留最新的6条
  if (recentArticles.value.length > MAX_RECENT_ARTICLES) {
    recentArticles.value = recentArticles.value.slice(0, MAX_RECENT_ARTICLES)
  }
  
  console.log('Updated recent articles:', recentArticles.value)
  
  // 保存到 localStorage
  try {
    localStorage.setItem(RECENT_ARTICLES_KEY, JSON.stringify(recentArticles.value))
    console.log('Saved recent articles to localStorage')
  } catch (e) {
    console.error('Failed to save recent articles:', e)
  }
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
  // 只有在props.loadData为true时才加载文档树
  if (!docTree.value && props.loadData) {
    await docStore.loadDocTree()
  }
  loadRecentArticles()
})
</script>

<style scoped>
.doc-tree {
  @apply h-full relative flex flex-col;
}

.nav-content {
  @apply flex-1 flex flex-col h-full transition-all duration-300 ease-in-out;
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
}

.section-title {
  @apply text-sm font-medium uppercase tracking-wider text-gray-500 mb-3 pl-1 dark:text-gray-400;
}

.tree-container {
  @apply flex-1 overflow-y-auto px-0 py-2;
  height: calc(100% - 2rem); /* 减去标题的高度 */
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

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
.dark ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}
.dark ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style> 