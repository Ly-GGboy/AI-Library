import { defineStore } from 'pinia'
import { ref } from 'vue'
import { docApi, type DocTree, type DocContent, type Breadcrumb } from '../services/api'

export const useDocStore = defineStore('doc', {
  state: () => ({
    docTree: null as DocTree | null,
    currentDoc: null as DocContent | null,
    recentDocs: [] as DocContent[],
    loading: false,
    error: null as string | null
  }),

  actions: {
    async loadDocTree() {
      this.loading = true
      this.error = null
      try {
        const result = await docApi.getDocTree()
        this.docTree = result
      } catch (err) {
        console.error('Error loading doc tree:', err)
        this.error = err instanceof Error ? err.message : '加载文档树失败'
      } finally {
        this.loading = false
      }
    },

    async loadDocContent(path: string) {
      this.loading = true
      this.error = null
      try {
        const doc = await docApi.getDocContent(path)
        this.currentDoc = doc
      } catch (err) {
        console.error('Error loading doc content:', err)
        this.error = err instanceof Error ? err.message : '加载文档内容失败'
      } finally {
        this.loading = false
      }
    },

    async loadRecentDocs() {
      this.loading = true
      this.error = null
      try {
        const result = await docApi.getRecentDocs()
        this.recentDocs = result
      } catch (err) {
        console.error('Error loading recent docs:', err)
        this.error = err instanceof Error ? err.message : '加载最近文档失败'
      } finally {
        this.loading = false
      }
    }
  }
}) 