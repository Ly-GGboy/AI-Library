<template>
  <div class="search-bar">
    <div class="relative">
      <input
        v-model="searchQuery"
        type="text"
        id="search-input"
        name="search"
        placeholder="搜索文档..."
        class="w-full px-4 py-2 rounded-full bg-gray-100 border-none focus:outline-none focus:ring-2 focus:ring-gray-200 text-sm transition-all dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400 dark:focus:ring-gray-600"
        @keydown.enter="onSearch"
      >
      <button 
        class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500"
        @click="onSearch"
      >
        <MagnifyingGlassIcon class="w-5 h-5" />
      </button>
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