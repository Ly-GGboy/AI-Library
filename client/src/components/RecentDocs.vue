<template>
  <div class="recent-docs">
    <div v-if="recentArticles.length === 0" class="empty">
      暂无最近访问的文档
    </div>
    <div v-else class="recent-list">
      <router-link
        v-for="article in recentArticles"
        :key="article.path"
        :to="{ name: 'doc', params: { path: article.path } }"
        class="recent-item"
        :class="{ 'active': isCurrentArticle(article.path) }"
      >
        <div class="item-content">
          <DocumentTextIcon v-if="article.type === 'pdf'" class="w-4 h-4 flex-shrink-0 mr-2" :class="isCurrentArticle(article.path) ? 'text-blue-500' : 'text-gray-400'" />
          <DocumentIcon v-else class="w-4 h-4 flex-shrink-0 mr-2" :class="isCurrentArticle(article.path) ? 'text-blue-500' : 'text-gray-400'" />
          <span class="item-name" :title="article.name">{{ article.name }}</span>
        </div>
        <span v-if="article.size" class="item-time">{{ getReadingTime(article) }}分钟</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { DocumentTextIcon, DocumentIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const RECENT_ARTICLES_KEY = 'recent-articles'
const recentArticles = ref<Array<{
  path: string, 
  name: string, 
  size?: number, 
  type?: 'markdown' | 'pdf', 
  page_count?: number
}>>([])

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

// 检查是否是当前文章
const isCurrentArticle = (path: string) => {
  return route.params.path === path
}

// 计算阅读时间
const getReadingTime = (article: {size?: number, name: string, type?: 'markdown' | 'pdf', page_count?: number}) => {
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

// 监听路由变化时重新加载最近访问
watch(() => route.params.path, () => {
  loadRecentArticles()
})

onMounted(() => {
  loadRecentArticles()
})
</script>

<style scoped>
.recent-docs {
  @apply flex flex-col;
}

.empty {
  @apply text-gray-500 dark:text-gray-400 text-center py-2 text-sm;
}

.recent-list {
  @apply space-y-1;
}

.recent-item {
  @apply flex items-center justify-between px-2 py-1.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors;
}

.recent-item.active {
  @apply bg-gray-100 dark:bg-gray-800 text-blue-700 dark:text-blue-400;
}

.item-content {
  @apply flex items-center flex-1 overflow-hidden;
}

.item-name {
  @apply truncate flex-1 mr-2;
}

.item-time {
  @apply text-xs text-gray-500 dark:text-gray-400 flex-shrink-0;
}
</style> 