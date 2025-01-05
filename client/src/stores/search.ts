import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchApi, type SearchResult } from '../services/api'

export const useSearchStore = defineStore('search', () => {
  const searchResults = ref<SearchResult[]>([])
  const suggestions = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 搜索文档
  async function search(query: string, limit: number = 10) {
    try {
      loading.value = true
      error.value = null
      console.log('Searching with query:', query)
      const results = await searchApi.search(query, limit)
      console.log('Search results:', results)
      searchResults.value = results
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Search failed'
      console.error('Search failed:', e)
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  // 获取搜索建议
  async function getSuggestions(query: string, limit: number = 5) {
    try {
      loading.value = true
      error.value = null
      console.log('Getting suggestions for query:', query)
      const results = await searchApi.getSuggestions(query, limit)
      console.log('Suggestions:', results)
      suggestions.value = results
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to get suggestions'
      console.error('Failed to get suggestions:', e)
      suggestions.value = []
    } finally {
      loading.value = false
    }
  }

  return {
    searchResults,
    suggestions,
    loading,
    error,
    search,
    getSuggestions
  }
}) 