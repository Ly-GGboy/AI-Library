<template>
  <div class="search-view dark:bg-gray-900">
    <header class="header dark:bg-gray-800">
      <div class="header-content">
        <router-link to="/" class="home-link">
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
      <SearchBar class="search" />
    </header>

    <main class="main">
      <div v-if="loading" class="loading">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>

      <div v-else-if="error" class="error dark:bg-red-900 dark:text-red-100">
        {{ error }}
      </div>

      <div v-else-if="searchResults.length === 0" class="no-results dark:text-gray-400">
        没有找到相关文档
      </div>

      <div v-else class="results">
        <div
          v-for="result in searchResults"
          :key="result.path"
          class="result-item dark:bg-gray-800"
        >
          <router-link
            :to="{ name: 'doc', params: { path: result.path } }"
            class="result-link"
          >
            <DocumentTextIcon class="result-icon dark:text-gray-500" />
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
              <span class="result-date dark:text-gray-500">{{ formatDate(result.last_modified) }}</span>
            </div>
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSearchStore } from '../stores/search'
import { useThemeStore } from '../stores/theme'
import { DocumentTextIcon, HomeIcon, SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import SearchBar from '../components/SearchBar.vue'
import { storeToRefs } from 'pinia'

const route = useRoute()
const searchStore = useSearchStore()
const themeStore = useThemeStore()
const { searchResults, loading, error } = storeToRefs(searchStore)
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore

const performSearch = async () => {
  const query = route.query.q as string
  console.log('Performing search with query:', query)
  if (query) {
    await searchStore.search(query)
    console.log('Search results:', searchResults.value)
  }
}

onMounted(performSearch)

watch(() => route.query.q, performSearch)

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.search-view {
  @apply min-h-screen bg-gray-50;
}

.header {
  @apply bg-white shadow-sm py-4 px-6;
}

.header-content {
  @apply flex items-center gap-4 mb-4;
}

.home-link {
  @apply flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors dark:text-gray-400 dark:hover:text-gray-200;
}

.home-icon {
  @apply w-5 h-5;
}

.home-text {
  @apply text-sm;
}

.title {
  @apply text-2xl font-bold text-gray-900;
}

.theme-toggle {
  @apply p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors;
}

.search {
  @apply max-w-2xl;
}

.main {
  @apply container mx-auto px-4 py-6;
}

.loading {
  @apply flex justify-center items-center py-8;
}

.error {
  @apply text-red-500 p-4 rounded bg-red-50 my-4;
}

.no-results {
  @apply text-gray-500 text-center py-8;
}

.results {
  @apply space-y-4;
}

.result-item {
  @apply bg-white rounded-lg shadow hover:shadow-md transition-shadow;
}

.result-link {
  @apply flex gap-4 p-4;
}

.result-icon {
  @apply w-6 h-6 text-gray-400 flex-shrink-0;
}

.result-content {
  @apply flex-grow;
}

.result-title {
  @apply text-lg font-medium text-gray-900 mb-2;
}

.result-matches {
  @apply space-y-2;
}

.match-item {
  @apply text-sm;
}

.match-type {
  @apply font-medium text-gray-700;
}

.match-text {
  @apply text-gray-600 mt-1;
}

.result-date {
  @apply text-sm text-gray-500 mt-2 block;
}
</style> 