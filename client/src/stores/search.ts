import { defineStore } from 'pinia'
import { ref } from 'vue'
import { searchDocs } from '../services/api'

interface SearchResult {
  path: string
  name: string
  matches: Array<{
    type: string
    text: string
    line: number
  }>
  relevance_score: number
}

interface SearchMeta {
  total: number
  total_matches: number
  page: number
  per_page: number
  total_pages: number
}

interface SearchParams {
  q: string
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: string
  doc_type?: string
}

export const useSearchStore = defineStore('search', () => {
  const searchResults = ref<SearchResult[]>([])
  const searchMeta = ref<SearchMeta>({
    total: 0,
    total_matches: 0,
    page: 1,
    per_page: 10,
    total_pages: 0
  })
  const loading = ref(false)
  const error = ref<string | null>(null)

  const search = async (params: SearchParams) => {
    loading.value = true
    error.value = null
    try {
      const response = await searchDocs(params)
      searchResults.value = response.results
      searchMeta.value = {
        total: response.total,
        total_matches: response.total_matches,
        page: response.page,
        per_page: response.per_page,
        total_pages: response.total_pages
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '搜索失败'
      searchResults.value = []
      searchMeta.value = {
        total: 0,
        total_matches: 0,
        page: 1,
        per_page: 10,
        total_pages: 0
      }
    } finally {
      loading.value = false
    }
  }

  return {
    searchResults,
    searchMeta,
    loading,
    error,
    search
  }
}) 