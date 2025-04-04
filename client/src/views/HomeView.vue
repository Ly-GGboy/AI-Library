<template>
  <div class="home dynamic-bg dark:bg-gray-900 min-h-screen">
    <!-- 顶部导航栏 -->
    <header class="glass sticky top-0 z-50 border-b border-gray-100 dark:border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-semibold tracking-tight text-gray-900 dark:text-gray-100">文档中心</h1>
            
            <!-- 在线阅读人数 -->
            <div class="ml-4 flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-full text-sm" title="当前在线阅读人数">
              <UserGroupIcon class="w-4 h-4 text-primary-500 mr-1" />
              <span class="font-medium text-primary-500">{{ onlineReadersCount }}</span>
              <span class="ml-1 hidden sm:inline">在线</span>
            </div>
            
            <a 
              href="https://github.com/Ly-GGboy/AI-Library" 
              target="_blank" 
              rel="noopener"
              class="ml-4 flex items-center text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
              title="查看GitHub源码"
            >
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.236 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
              </svg>
            </a>
          </div>
          
          <!-- 搜索框调整到中间位置 -->
          <div class="flex-1 max-w-xl mx-auto">
            <SearchBar class="search" @search="onSearch" />
          </div>
          
          <!-- 右侧操作按钮 -->
          <div class="flex items-center justify-end space-x-4">
            <AnnouncementButton 
              @click="openAnnouncementBoard" 
              :has-new-updates="hasNewUpdates" 
              class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            />
            <button
              @click="toggleTheme"
              @mouseenter="themeButtonHover = true"
              @mouseleave="themeButtonHover = false"
              class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
            >
              <Transition name="icon-switch" mode="out-in">
                <SunIcon v-if="isDark" key="sun" class="w-5 h-5 text-gray-500 dark:text-gray-400" />
                <MoonIcon v-else key="moon" class="w-5 h-5 text-gray-500 dark:text-gray-400" />
              </Transition>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <!-- 顶部横幅 -->
      <div class="mb-8 text-center">
        <h1 class="text-4xl font-bold tracking-tight mb-3 text-gray-900 dark:text-gray-100">你的知识库</h1>
        <p class="text-xl text-gray-500 dark:text-gray-400 max-w-3xl mx-auto">探索、阅读和管理你的文档，随时随地获取知识</p>
      </div>
      
      <!-- 内容区域 -->
      <div class="flex gap-8">
        <!-- 左侧边栏 - 文件导航 -->
        <div class="w-80 flex-shrink-0">
          <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 h-[calc(100vh-16rem)] overflow-hidden">
            <DocTree :load-data="false" class="h-full" />
          </div>
        </div>
        
        <!-- 主内容区 -->
        <div class="flex-1">
          <!-- 最近更新标题 -->
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{{ activeTab === 'recent' ? '最近更新' : '最近访问' }}</h2>
            <div class="flex space-x-2">
              <button 
                class="px-3 py-1.5 text-sm rounded-full transition-colors"
                :class="activeTab === 'recent' ? 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300' : 'hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400'"
                @click="activeTab = 'recent'"
              >
                最近更新
              </button>
              <button 
                class="px-3 py-1.5 text-sm rounded-full transition-colors"
                :class="activeTab === 'visited' ? 'bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300' : 'hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400'"
                @click="activeTab = 'visited'"
              >
                最近访问
              </button>
            </div>
          </div>
          
          <!-- 加载中状态 -->
          <div v-if="loading" class="loading flex justify-center items-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          </div>
          
          <!-- 错误状态 -->
          <div v-else-if="error" class="error text-red-500 p-4 rounded bg-red-50 dark:bg-red-900/20 dark:text-red-400 my-4">
            {{ error }}
          </div>
          
          <!-- 最近更新文档网格 -->
          <div v-else-if="activeTab === 'recent'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <router-link
              v-for="(doc, index) in recentDocs.slice(0, 6)"
              :key="doc.path"
              :to="{ name: 'doc', params: { path: doc.path } }"
              class="doc-card bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden"
            >
              <div :class="[
                'h-40 bg-gradient-to-r flex items-center justify-center',
                getGradientClass(index)
              ]">
                <component 
                  :is="getRandomIcon(index)" 
                  class="w-16 h-16"
                  :class="getIconColorClass(index)"
                />
              </div>
              <div class="p-5">
                <h3 class="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100 line-clamp-1">{{ doc.name.replace('.md', '') }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">
                  <span>{{ formatDate(doc.last_modified) }}</span>
                  <span class="mx-2">·</span>
                  <span>{{ getTimeAgo(doc.last_modified) }}</span>
                </p>
                <div class="flex items-center justify-between mt-4">
                  <span class="text-xs text-gray-500 dark:text-gray-400">约 {{ getReadingTime(doc) }} 分钟阅读</span>
                </div>
              </div>
            </router-link>
            
            <!-- 空状态 -->
            <div v-if="recentDocs.length === 0" class="empty text-gray-500 dark:text-gray-400 text-center py-8 col-span-3">
              暂无最近更新的文档
            </div>
          </div>
          
          <!-- 最近访问文档网格 -->
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <router-link
              v-for="(article, index) in recentArticles"
              :key="article.path"
              :to="{ name: 'doc', params: { path: article.path } }"
              class="doc-card bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden"
            >
              <div :class="[
                'h-40 bg-gradient-to-r flex items-center justify-center',
                getVisitedGradientClass(index)
              ]">
                <component 
                  :is="getVisitedRandomIcon(index, article.type)" 
                  class="w-16 h-16"
                  :class="getVisitedIconColorClass(index)"
                />
              </div>
              <div class="p-5">
                <h3 class="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100 line-clamp-1">{{ article.name }}</h3>
                <div class="flex items-center justify-between mt-4">
                  <span class="text-xs text-gray-500 dark:text-gray-400">最近访问</span>
                  <span v-if="article.size" class="text-xs text-gray-500 dark:text-gray-400">约 {{ getArticleReadingTime(article) }} 分钟阅读</span>
                </div>
              </div>
            </router-link>
            
            <!-- 空状态 -->
            <div v-if="recentArticles.length === 0" class="empty text-gray-500 dark:text-gray-400 text-center py-8 col-span-3">
              暂无最近访问的文档
            </div>
          </div>
        </div>
      </div>
    </div>

    <AnnouncementBoard ref="announcementBoardRef" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, ref, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocStore } from '../stores/doc'
import { useThemeStore } from '../stores/theme'
import { useAnnouncementStore } from '../stores/announcement'
import {
  DocumentTextIcon,
  BookOpenIcon,
  AcademicCapIcon,
  BeakerIcon,
  ChartBarIcon,
  CircleStackIcon,
  CloudIcon,
  CodeBracketIcon,
  CommandLineIcon,
  CpuChipIcon,
  CubeIcon,
  GlobeAltIcon,
  ServerIcon,
  SparklesIcon,
  VariableIcon,
  SunIcon,
  MoonIcon,
  UserGroupIcon
} from '@heroicons/vue/24/outline'
import SearchBar from '../components/SearchBar.vue'
import DocTree from '../components/DocTree.vue'
import AnnouncementButton from '../components/announcement/AnnouncementButton.vue'
import AnnouncementBoard from '../components/announcement/AnnouncementBoard.vue'
import { storeToRefs } from 'pinia'
import type { DocTree as DocTreeType, DocContent } from '../services/api'
import { docApi } from '../services/api'
import type { ComponentPublicInstance } from 'vue'

const route = useRoute()
const router = useRouter()
const docStore = useDocStore()
const themeStore = useThemeStore()
const announcementStore = useAnnouncementStore()
const { recentDocs, loading, error, docTree } = storeToRefs(docStore)
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore
const { hasNewUpdates } = storeToRefs(announcementStore)
const themeButtonHover = ref(false)

// 在线阅读人数
const onlineReadersCount = ref(0)
let onlineReadersTimer: any = null

const fetchOnlineReadersCount = async () => {
  try {
    const response = await docApi.getOnlineReadersCount()
    onlineReadersCount.value = response.count
  } catch (error) {
    console.error('获取在线阅读人数失败:', error)
  }
}

// 标签页切换
const activeTab = ref('recent') // 'recent' 或 'visited'

// 最近访问的文章
const recentArticles = ref<Array<{path: string, name: string, size?: number, type?: 'markdown' | 'pdf', page_count?: number}>>([])
const RECENT_ARTICLES_KEY = 'recent-articles'
const MAX_RECENT_ARTICLES = 6

// 从 localStorage 加载最近访问的文章
const loadRecentArticles = () => {
  const saved = localStorage.getItem(RECENT_ARTICLES_KEY)
  console.log('Loading recent articles from localStorage:', saved)
  if (saved) {
    try {
      recentArticles.value = JSON.parse(saved)
      console.log('Parsed recent articles:', recentArticles.value)
    } catch (e) {
      console.error('Failed to parse recent articles:', e)
      recentArticles.value = []
    }
  }
}

// 添加文章到最近访问
const addToRecentArticles = (path: string, name: string, metadata?: {size?: number, type?: 'markdown' | 'pdf', page_count?: number}) => {
  if (!path || !name) return
  
  const article = { 
    path, 
    name,
    size: metadata?.size,
    type: metadata?.type,
    page_count: metadata?.page_count
  }
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

const announcementBoardRef = ref<ComponentPublicInstance & { openBoard: () => void } | null>(null)

const openAnnouncementBoard = () => {
  if (announcementBoardRef.value) {
    announcementBoardRef.value.openBoard()
    announcementStore.markUpdatesAsViewed()
  }
}

onMounted(async () => {
  // 同时加载文档树和最近文档，避免重复加载
  await Promise.all([
    docStore.loadDocTree(),
    docStore.loadRecentDocs()
  ]);
  
  // 加载最近访问的文章
  loadRecentArticles();
  
  // 加载更新信息
  try {
    await announcementStore.getUpdates()
  } catch (err) {
    console.error('Failed to load updates:', err)
  }
  
  // 如果有 hash，跳转到对应的目录
  if (route.hash) {
    const path = route.hash.slice(1) // 移除 # 符号
    const node = docTree.value && findNodeByPath(docTree.value, path)
    if (node) {
      // 展开对应的目录
      const storageKey = `tree-node-${path}`
      localStorage.setItem(storageKey, 'true')
    }
  }
  
  // 获取在线阅读人数
  fetchOnlineReadersCount();
  // 设置定时刷新
  onlineReadersTimer = setInterval(fetchOnlineReadersCount, 60000); // 每分钟更新一次
})

// 在组件卸载时清除定时器
onUnmounted(() => {
  if (onlineReadersTimer) {
    clearInterval(onlineReadersTimer);
    onlineReadersTimer = null;
  }
})

// 监听 hash 变化
watch(() => route.hash, (newHash) => {
  if (newHash) {
    const path = newHash.slice(1)
    const node = docTree.value && findNodeByPath(docTree.value, path)
    if (node) {
      // 展开对应的目录
      const storageKey = `tree-node-${path}`
      localStorage.setItem(storageKey, 'true')
    }
  }
})

// 监听标签页切换
watch(activeTab, (newTab) => {
  console.log('Tab changed to:', newTab)
  if (newTab === 'visited') {
    loadRecentArticles()
    console.log('Current recent articles:', recentArticles.value)
  }
})

// 在路由变化时更新最近访问记录
watch(() => route.params.path, (newPath) => {
  if (typeof newPath === 'string' && docTree.value) {
    // 从文档树中查找文章信息
    const findArticleInfo = (node: DocTreeType, path: string): {name: string, size?: number, type?: 'markdown' | 'pdf', page_count?: number} | null => {
      if (node.path === path) {
        return {
          name: node.name.replace(/\.(md|pdf)$/, ''),
          size: node.size,
          type: node.type as 'markdown' | 'pdf' | undefined,
          page_count: node.page_count
        }
      }
      if (node.children) {
        for (const child of node.children) {
          const found = findArticleInfo(child, path)
          if (found) return found
        }
      }
      return null
    }

    const articleInfo = findArticleInfo(docTree.value, newPath)
    if (articleInfo) {
      addToRecentArticles(newPath, articleInfo.name, {
        size: articleInfo.size,
        type: articleInfo.type,
        page_count: articleInfo.page_count
      })
    }
  }
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 递归查找节点
const findNodeByPath = (node: DocTreeType, path: string): DocTreeType | null => {
  if (!node) return null
  if (node.path === path) return node
  if (node.children) {
    for (const child of node.children) {
      const found = findNodeByPath(child, path)
      if (found) return found
    }
  }
  return null
}

// 获取渐变背景类名
const getGradientClass = (index: number) => {
  const gradients = [
    'from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20',
    'from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20',
    'from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20',
    'from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20',
    'from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20',
    'from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20'
  ]
  return gradients[index % gradients.length]
}

// 获取图标颜色类名
const getIconColorClass = (index: number) => {
  const colors = [
    'text-blue-400 dark:text-blue-500',
    'text-green-400 dark:text-green-500',
    'text-purple-400 dark:text-purple-500',
    'text-yellow-400 dark:text-yellow-500',
    'text-red-400 dark:text-red-500',
    'text-cyan-400 dark:text-cyan-500'
  ]
  return colors[index % colors.length]
}

// 获取随机图标
const getRandomIcon = (index: number) => {
  const icons = [
    DocumentTextIcon,
    BookOpenIcon,
    CodeBracketIcon,
    CommandLineIcon,
    CpuChipIcon,
    ServerIcon,
    CloudIcon
  ]
  return icons[index % icons.length]
}

// 获取相对时间
const getTimeAgo = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (days > 0) return `${days} 天前更新`
  if (hours > 0) return `${hours} 小时前更新`
  if (minutes > 0) return `${minutes} 分钟前更新`
  return '刚刚更新'
}

// 估算阅读时间
const getReadingTime = (doc: DocContent) => {
  // 如果没有大小信息，返回默认值
  if (!doc.size) {
    return 1;
  }
  
  // PDF和MD文件使用不同的计算方式
  if (doc.type === 'pdf') {
    // PDF文件：假设每页大约2分钟，如果有页数信息则使用
    if (doc.page_count) {
      return Math.max(1, Math.ceil(doc.page_count * 2));
    }
    
    // 如果没有页数信息，按照大小估算
    // 平均每页约100KB
    const estimatedPages = Math.ceil(doc.size / (100 * 1024));
    return Math.max(1, estimatedPages * 2);
  } else {
    // Markdown文件：按照文本内容计算
    // 假设平均每个中文字符占3字节，每分钟阅读300个字
    const charsPerByte = 1/3;  // 每字节对应的字符数
    const wordsPerMinute = 300;
    const charCount = doc.size * charsPerByte;
    const minutes = Math.ceil(charCount / wordsPerMinute);
    return Math.max(1, minutes); // 至少1分钟
  }
}

// 获取最近访问的渐变背景类名
const getVisitedGradientClass = (index: number) => {
  const gradients = [
    'from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20',
    'from-cyan-50 to-blue-50 dark:from-cyan-900/20 dark:to-blue-900/20',
    'from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20',
    'from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20',
    'from-red-50 to-rose-50 dark:from-red-900/20 dark:to-rose-900/20',
    'from-indigo-50 to-violet-50 dark:from-indigo-900/20 dark:to-violet-900/20'
  ]
  return gradients[index % gradients.length]
}

// 获取最近访问的图标颜色类名
const getVisitedIconColorClass = (index: number) => {
  const colors = [
    'text-purple-400 dark:text-purple-500',
    'text-cyan-400 dark:text-cyan-500',
    'text-yellow-400 dark:text-yellow-500',
    'text-green-400 dark:text-green-500',
    'text-red-400 dark:text-red-500',
    'text-indigo-400 dark:text-indigo-500'
  ]
  return colors[index % colors.length]
}

// 获取最近访问的随机图标
const getVisitedRandomIcon = (index: number, type?: string) => {
  // 对于PDF文件，固定使用DocumentTextIcon
  if (type === 'pdf') {
    return DocumentTextIcon;
  }
  
  // 其他类型使用随机图标
  const icons = [
    AcademicCapIcon,
    BeakerIcon,
    ChartBarIcon,
    CircleStackIcon,
    CloudIcon,
    CodeBracketIcon,
    CommandLineIcon,
    CpuChipIcon,
    CubeIcon,
    GlobeAltIcon,
    ServerIcon,
    SparklesIcon,
    VariableIcon,
    BookOpenIcon,
  ]
  // 使用 index 作为种子来保证每次渲染相同位置的图标都是一样的
  const randomIndex = Math.abs(Math.sin(index + 1) * icons.length) | 0
  return icons[randomIndex]
}

// 处理搜索
const onSearch = (query: string) => {
  router.push({
    name: 'search',
    query: { q: query }
  })
}

// 估算文章阅读时间
const getArticleReadingTime = (article: {size?: number, name: string, type?: 'markdown' | 'pdf', page_count?: number}) => {
  // 如果没有大小信息，返回默认值
  if (!article.size) {
    return 1;
  }
  
  // 根据文件类型使用不同的计算方法
  if (article.type === 'pdf') {
    // PDF文件：假设每页大约2分钟，如果有页数信息则使用
    if (article.page_count) {
      return Math.max(1, Math.ceil(article.page_count * 2));
    }
    
    // 如果没有页数信息，按照大小估算
    // 平均每页约100KB
    const estimatedPages = Math.ceil(article.size / (100 * 1024));
    return Math.max(1, estimatedPages * 2);
  } else {
    // Markdown文件：按照文本内容计算
    // 假设平均每个中文字符占3字节，每分钟阅读300个字
    const charsPerByte = 1/3;  // 每字节对应的字符数
    const wordsPerMinute = 300;
    const charCount = article.size * charsPerByte;
    const minutes = Math.ceil(charCount / wordsPerMinute);
    return Math.max(1, minutes); // 至少1分钟
  }
}
</script>

<style scoped>
/* 全局样式 */
.home {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* 文档卡片悬浮效果 */
.doc-card {
  transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.doc-card:hover {
  transform: scale(1.02);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.01);
}

/* 毛玻璃效果 */
.glass {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark .glass {
  background: rgba(31, 41, 55, 0.8);
}

/* 动态背景渐变 */
.dynamic-bg {
  background: linear-gradient(120deg, #f8f9fa, #ffffff);
  background-size: 200% 200%;
  animation: gradientAnimation 15s ease infinite;
}

.dark .dynamic-bg {
  background: linear-gradient(120deg, #1f2937, #111827);
  background-size: 200% 200%;
  animation: gradientAnimation 15s ease infinite;
}

@keyframes gradientAnimation {
  0% { background-position: 0% 50% }
  50% { background-position: 100% 50% }
  100% { background-position: 0% 50% }
}

/* 图标切换动画 */
.icon-switch-enter-active,
.icon-switch-leave-active {
  transition: all 0.2s ease;
}

.icon-switch-enter-from,
.icon-switch-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(15deg);
}
</style> 