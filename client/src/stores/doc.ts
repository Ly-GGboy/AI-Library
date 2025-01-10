import { defineStore } from 'pinia'
import { ref } from 'vue'
import { docApi, type DocTree, type DocContent, type Breadcrumb } from '../services/api'

export const useDocStore = defineStore('doc', () => {
  const docTree = ref<DocTree | null>(null)
  const currentDoc = ref<DocContent | null>(null)
  const breadcrumb = ref<Breadcrumb[]>([])
  const recentDocs = ref<DocContent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 加载文档树
  async function loadDocTree() {
    try {
      loading.value = true
      error.value = null
      const result = await docApi.getDocTree()
      console.log('Loaded doc tree:', result)
      docTree.value = result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load document tree'
      console.error('Failed to load document tree:', e)
    } finally {
      loading.value = false
    }
  }

  // 加载文档内容
  async function loadDocContent(path: string) {
    try {
      loading.value = true
      error.value = null
      console.log('Loading doc content for path:', path)
      
      // 重置当前文档，避免显示旧内容
      currentDoc.value = null
      
      const doc = await docApi.getDocContent(path)
      console.log('Loaded doc content:', doc)
      
      if (!doc) {
        throw new Error('Document not found')
      }
      
      currentDoc.value = doc
      breadcrumb.value = await docApi.getBreadcrumb(path)
      console.log('Current doc after loading:', currentDoc.value)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load document'
      console.error('Failed to load document:', e)
      currentDoc.value = null
    } finally {
      loading.value = false
    }
  }

  // 加载最近文档
  async function loadRecentDocs(limit: number = 10) {
    try {
      loading.value = true
      error.value = null
      const result = await docApi.getRecentDocs(limit)
      console.log('Loaded recent docs:', result)
      recentDocs.value = result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load recent documents'
      console.error('Failed to load recent documents:', e)
    } finally {
      loading.value = false
    }
  }

  // 初始化 store
  async function init() {
    try {
      await loadDocTree()
      await loadRecentDocs()
    } catch (e) {
      console.error('Failed to initialize doc store:', e)
    }
  }

  // 自动初始化
  init()

  return {
    docTree,
    currentDoc,
    breadcrumb,
    recentDocs,
    loading,
    error,
    loadDocTree,
    loadDocContent,
    loadRecentDocs
  }
}) 