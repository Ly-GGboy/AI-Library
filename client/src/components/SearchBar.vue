<template>
  <div class="search-bar">
    <div class="relative flex items-center">
      <input
        type="text"
        v-model="searchQuery"
        :placeholder="placeholder"
        class="w-full px-4 py-2 pl-10 pr-12 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 placeholder-gray-400 dark:placeholder-gray-500"
        @keyup.enter="onSearch"
      />
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg class="h-5 w-5 text-gray-400 dark:text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
        </svg>
      </div>
      <button
        v-if="searchQuery"
        class="absolute right-3 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
        @click="clearSearch"
      >
        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  initialQuery?: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'search', query: string): void
  (e: 'update:modelValue', value: string): void
}>()

const searchQuery = ref(props.initialQuery || '')

// 处理搜索
const onSearch = () => {
  if (searchQuery.value.trim()) {
    emit('search', searchQuery.value)
  }
}

// 清除搜索
const clearSearch = () => {
  searchQuery.value = ''
  emit('update:modelValue', '')
}

// 监听初始查询变化
watch(() => props.initialQuery, (newQuery) => {
  if (newQuery !== undefined) {
    searchQuery.value = newQuery
  }
})

// 监听搜索框值变化
watch(searchQuery, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>

<style scoped>
.search-bar {
  @apply relative w-full;
}
</style> 