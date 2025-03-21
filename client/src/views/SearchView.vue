<template>
  <div class="search-view dark:bg-gray-800">
    <!-- 顶部导航栏 - 毛玻璃效果 -->
    <header class="header glass-effect dark:glass-effect-dark sticky top-0 z-10">
      <div class="header-content max-w-7xl mx-auto">
        <router-link to="/" class="home-link" @click="clearSearchParams">
          <HomeIcon class="home-icon" />
          <span class="home-text">首页</span>
        </router-link>
        <h1 class="title dark:text-gray-100">搜索结果</h1>
        <button
          @click="toggleTheme"
          class="theme-toggle ml-auto"
          :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
        >
          <SunIcon v-if="isDark" class="w-5 h-5 text-gray-400 hover:text-gray-300" />
          <MoonIcon v-else class="w-5 h-5 text-gray-600 hover:text-gray-700" />
        </button>
      </div>
      
      <!-- 搜索栏 - 大圆角 -->
      <div class="max-w-3xl mx-auto px-4">
        <SearchBar :initial-query="searchQuery" @search="onSearch" class="search-bar-container" />
      </div>
      
      <!-- 高级搜索选项 - 毛玻璃卡片 -->
      <div class="advanced-search max-w-3xl mx-auto mt-4 px-4">
        <div class="glass-card dark:glass-card-dark">
          <div class="flex flex-wrap gap-3">
            <select v-model="searchParams.doc_type" class="form-select" @change="onDocTypeChange($event)">
              <option value="all">所有文档类型</option>
              <option value="md">Markdown</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
        </div>
      </div>
    </header>

    <main class="main max-w-5xl mx-auto px-4 py-6">
      <!-- 加载状态 - 苹果风格加载动画 -->
      <div v-if="loading" class="loading">
        <div class="apple-spinner"></div>
      </div>

      <!-- 错误提示 - 圆角卡片 -->
      <div v-else-if="error" class="error glass-card-error dark:glass-card-error-dark">
        <ExclamationCircleIcon class="w-5 h-5 text-red-500 dark:text-red-400 mr-2" />
        {{ error }}
      </div>

      <!-- 无结果提示 - 圆角卡片 -->
      <div v-else-if="searchResults.length === 0" class="no-results glass-card dark:glass-card-dark">
        <DocumentIcon class="w-8 h-8 text-gray-400 dark:text-gray-500 mb-2" />
        <p>没有找到相关文档</p>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">请尝试其他关键词或调整搜索条件</p>
      </div>

      <div v-else>
        <!-- 搜索统计 - 毛玻璃小卡片 -->
        <div class="search-stats glass-pill dark:glass-pill-dark">
          找到 {{ searchMeta.total }} 个文档，共 {{ searchMeta.total_matches }} 处匹配
        </div>
        
        <!-- 搜索结果列表 - 圆角卡片 -->
        <div class="results mt-4">
          <div
            v-for="result in searchResults"
            :key="result.path"
            class="result-item glass-card dark:glass-card-dark"
          >
            <router-link
              :to="{ name: 'doc', params: { path: result.path } }"
              class="result-link"
            >
              <div class="result-icon-container">
                <DocumentTextIcon class="result-icon" />
              </div>
              <div class="result-content">
                <h3 class="result-title dark:text-gray-100">{{ result.name }}</h3>
                <div class="result-matches">
                  <div
                    v-for="(match, index) in result.matches"
                    :key="index"
                    class="match-item"
                  >
                    <span class="match-type dark:text-gray-300">
                      {{ match.type === 'title' ? '标题' : '内容' }}:
                    </span>
                    <p class="match-text dark:text-gray-400">{{ match.text }}</p>
                  </div>
                </div>
              </div>
            </router-link>
          </div>
        </div>
        
        <!-- 分页控件 - 苹果风格按钮 -->
        <div v-if="searchMeta.total_pages > 1" class="pagination mt-8 flex justify-center gap-2">
          <button
            class="page-btn"
            :disabled="searchParams.page === 1"
            @click="changePage(searchParams.page - 1)"
          >
            <ChevronLeftIcon class="w-5 h-5" />
          </button>
          
          <template v-for="pageNum in displayedPageNumbers" :key="pageNum">
            <span v-if="pageNum === '...'" class="page-ellipsis">...</span>
            <button
              v-else
              class="page-num"
              :class="{ active: pageNum === searchParams.page }"
              @click="changePage(Number(pageNum))"
            >
              {{ pageNum }}
            </button>
          </template>
          
          <button
            class="page-btn"
            :disabled="searchParams.page === searchMeta.total_pages"
            @click="changePage(searchParams.page + 1)"
          >
            <ChevronRightIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSearchStore } from '../stores/search'
import { useThemeStore } from '../stores/theme'
import { 
  DocumentTextIcon, 
  HomeIcon, 
  SunIcon, 
  MoonIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  DocumentIcon,
  ExclamationCircleIcon
} from '@heroicons/vue/24/outline'
import SearchBar from '../components/SearchBar.vue'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const searchStore = useSearchStore()
const themeStore = useThemeStore()
const { searchResults, loading, error, searchMeta } = storeToRefs(searchStore)
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore

const searchQuery = ref(route.query.q as string || '')
const searchParams = ref({
  q: searchQuery.value,
  page: 1,
  per_page: 10,
  sort_by: 'relevance',
  sort_order: 'desc',
  doc_type: 'all'
})

// 计算要显示的页码
const displayedPageNumbers = computed(() => {
  const currentPage = searchStore.searchMeta.page
  const totalPages = searchStore.searchMeta.total_pages
  const delta = 2 // 当前页前后显示的页数
  
  const range: (number | string)[] = []
  for (let i = Math.max(1, currentPage - delta); i <= Math.min(totalPages, currentPage + delta); i++) {
    range.push(i)
  }
  
  const firstNum = range[0] as number
  const lastNum = range[range.length - 1] as number
  
  if (firstNum > 1) {
    range.unshift(1)
    if (firstNum > 2) {
      range.splice(1, 0, '...')
    }
  }
  
  if (lastNum < totalPages) {
    if (lastNum < totalPages - 1) {
      range.push('...')
    }
    range.push(totalPages)
  }
  
  return range
})

// 高亮搜索匹配文本
const highlightMatch = (text: string) => {
  if (!searchQuery.value) return text
  const regex = new RegExp(`(${searchQuery.value})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// 执行搜索
const performSearch = async () => {
  await searchStore.search(searchParams.value)
}

// 处理搜索事件
const onSearch = (query: string) => {
  searchParams.value = {
    ...searchParams.value,
    q: query,
    page: 1 // 重置页码
  }
  performSearch()
}

// 切换页码
const changePage = (page: number) => {
  if (typeof page === 'number') {
    searchParams.value.page = page
    performSearch()
  }
}

// 处理文档类型变化
const onDocTypeChange = (event: Event) => {
  const newType = (event.target as HTMLSelectElement).value
  searchParams.value = {
    ...searchParams.value,
    doc_type: newType,
    page: 1 // 重置页码
  }
  performSearch()
}

// 只在初始加载时执行一次搜索
onMounted(() => {
  if (searchQuery.value) {
    performSearch()
  }
})

const clearSearchParams = () => {
  window.location.href = '/'
}
</script>

<style scoped>
/* 基础样式 */
.search-view {
  @apply min-h-screen bg-gray-50 dark:bg-gray-800;
}

/* 毛玻璃效果 */
.glass-effect {
  @apply bg-white/80 backdrop-blur-lg border-b border-gray-200/50;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
}

.glass-effect-dark {
  @apply bg-gray-700/80 backdrop-blur-lg border-b border-gray-600/50;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
}

.glass-card {
  @apply bg-white/90 backdrop-blur-md rounded-xl shadow-sm border border-gray-100/50 p-4;
  transition: all 0.3s ease;
}

.glass-card-dark {
  @apply bg-gray-700/90 backdrop-blur-md rounded-xl shadow-sm border border-gray-600/50 p-4;
  transition: all 0.3s ease;
}

.glass-card-error {
  @apply bg-red-50/90 backdrop-blur-md rounded-xl shadow-sm border border-red-100/50 p-4 flex items-center;
}

.glass-card-error-dark {
  @apply bg-red-800/30 backdrop-blur-md rounded-xl shadow-sm border border-red-700/50 p-4 flex items-center text-red-100;
}

.glass-pill {
  @apply bg-white/90 backdrop-blur-md rounded-full shadow-sm border border-gray-100/50 px-4 py-2 text-sm text-gray-600 inline-flex;
}

.glass-pill-dark {
  @apply bg-gray-700/90 backdrop-blur-md rounded-full shadow-sm border border-gray-600/50 px-4 py-2 text-sm text-gray-300 inline-flex;
}

/* 头部样式 */
.header {
  @apply py-4 px-6;
}

.header-content {
  @apply flex items-center gap-4 mb-4;
}

.home-link {
  @apply flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors dark:text-gray-300 dark:hover:text-white;
}

.home-icon {
  @apply w-5 h-5;
}

.home-text {
  @apply text-sm;
}

.title {
  @apply text-2xl font-bold text-gray-900 dark:text-white;
}

.theme-toggle {
  @apply p-2 rounded-full hover:bg-gray-100/50 dark:hover:bg-gray-600/50 transition-colors;
}

.search-bar-container {
  @apply w-full;
}

/* 主体内容 */
.main {
  @apply pt-8;
}

/* 加载动画 - 苹果风格 */
.loading {
  @apply flex justify-center items-center py-12;
}

.apple-spinner {
  @apply relative w-12 h-12;
  border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: #3b82f6;
  animation: spin 1s linear infinite;
}

.apple-spinner:before {
  content: '';
  @apply absolute top-1 left-1 right-1 bottom-1 rounded-full;
  border: 2px solid transparent;
  border-top-color: #60a5fa;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误和无结果 */
.error {
  @apply my-8;
}

.no-results {
  @apply flex flex-col items-center justify-center py-12 my-8 text-gray-500 dark:text-gray-300;
}

/* 搜索结果 */
.results {
  @apply space-y-4;
}

.result-item {
  @apply hover:shadow-md transition-all hover:bg-white/100 dark:hover:bg-gray-700/100;
}

.result-item:hover {
  transform: translateY(-2px);
}

.result-link {
  @apply flex gap-4;
}

.result-icon-container {
  @apply flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-800/30 rounded-full flex items-center justify-center;
}

.result-icon {
  @apply w-5 h-5 text-blue-500 dark:text-blue-300;
}

.result-content {
  @apply flex-grow;
}

.result-title {
  @apply text-lg font-medium text-gray-900 dark:text-white mb-2;
}

.result-matches {
  @apply space-y-3;
}

.match-item {
  @apply text-sm bg-gray-50/80 dark:bg-gray-600/50 rounded-lg p-3;
}

.match-type {
  @apply font-medium text-gray-700 dark:text-gray-200;
}

.match-text {
  @apply text-gray-600 dark:text-gray-300 mt-1;
}

/* 表单元素 */
.form-select,
.form-input {
  @apply px-4 py-2 bg-white/90 dark:bg-gray-700/90 backdrop-blur-md border border-gray-200/50 dark:border-gray-600/50 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:focus:ring-blue-400/50 focus:border-blue-500/50 dark:focus:border-blue-400/50 transition-all dark:text-white;
}

.form-select::placeholder,
.form-input::placeholder {
  @apply text-gray-400 dark:text-gray-500;
}

/* 分页 */
.pagination {
  @apply flex items-center justify-center gap-2 mt-8;
}

.page-btn {
  @apply w-10 h-10 rounded-full flex items-center justify-center bg-white/90 dark:bg-gray-700/90 backdrop-blur-md border border-gray-200/50 dark:border-gray-600/50 text-gray-600 dark:text-gray-300
    hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all;
}

.page-ellipsis {
  @apply px-2 text-gray-500 dark:text-gray-400;
}

.page-num {
  @apply w-10 h-10 rounded-full flex items-center justify-center text-sm bg-white/90 dark:bg-gray-700/90 backdrop-blur-md border border-gray-200/50 dark:border-gray-600/50 text-gray-600 dark:text-gray-300
    hover:bg-gray-50 dark:hover:bg-gray-600 transition-all;
}

.page-num.active {
  @apply bg-blue-500 text-white border-blue-500 dark:bg-blue-600 dark:border-blue-600;
}

/* 高级搜索 */
.advanced-search {
  @apply pb-4;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .advanced-search .flex {
    @apply flex-col;
  }
  
  .form-select, .form-input {
    @apply w-full;
  }
}

/* 高亮匹配文本 */
mark {
  @apply bg-yellow-200 dark:bg-yellow-600/70 px-1 rounded text-gray-900 dark:text-yellow-50;
}
</style> 