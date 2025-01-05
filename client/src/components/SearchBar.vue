<template>
  <div class="search-bar">
    <div class="relative">
      <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
      <input
        v-model="searchQuery"
        type="text"
        id="search-input"
        name="search"
        placeholder="搜索文档..."
        class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
        @keydown.enter="onSearch"
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const searchQuery = ref('')

const onSearch = async () => {
  if (searchQuery.value) {
    await router.push({
      name: 'search',
      query: { q: searchQuery.value }
    })
  }
}
</script>

<style scoped>
.search-bar {
  @apply w-full max-w-xl mx-auto;
}
</style> 