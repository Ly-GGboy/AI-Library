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
        <DocumentTextIcon class="w-4 h-4 flex-shrink-0 mr-2" :class="isCurrentArticle(article.path) ? 'text-blue-500' : 'text-gray-400'" />
        <span class="item-name" :title="article.name">{{ article.name }}</span>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const RECENT_ARTICLES_KEY = 'recent-articles'
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

// 检查是否是当前文章
const isCurrentArticle = (path: string) => {
  return route.params.path === path
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
  @apply flex items-center px-2 py-1.5 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors;
}

.recent-item.active {
  @apply bg-gray-100 dark:bg-gray-800 text-blue-700 dark:text-blue-400;
}

.item-name {
  @apply truncate;
}
</style> 