import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchApi, type SearchResult } from '../services/api'

export const useSearchStore = defineStore('search', {
  state: () => ({
    searchResults: [] as SearchResult[],
    loading: false,
    error: null as string | null,
    suggestions: [] as string[]
  }),

  actions: {
    async search(query: string) {
      this.loading = true
      this.error = null
      try {
        const results = await searchApi.search(query)
        this.searchResults = results
      } catch (err) {
        console.error('Search error:', err)
        this.error = err instanceof Error ? err.message : '搜索失败'
      } finally {
        this.loading = false
      }
    },

    async getSuggestions(query: string) {
      try {
        const results = await searchApi.getSuggestions(query)
        this.suggestions = results
      } catch (err) {
        console.error('Error getting suggestions:', err)
        this.suggestions = []
      }
    }
  }
}) 