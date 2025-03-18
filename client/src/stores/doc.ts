import { defineStore } from 'pinia'
import { ref } from 'vue'
import { docApi, type DocTree, type DocContent, type Breadcrumb } from '../services/api'

export const useDocStore = defineStore('doc', {
  state: () => ({
    docTree: null as DocTree | null,
    currentDoc: null as DocContent | null,
    recentDocs: [] as DocContent[],
    loading: false,
    subTreeLoading: {} as Record<string, boolean>,
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

    async loadDocSubtree(path: string) {
      // 设置特定路径的加载状态
      this.subTreeLoading[path] = true
      
      try {
        const subtree = await docApi.getDocSubtree(path)
        
        // 递归函数查找目标节点
        const updateNode = (node: DocTree, targetPath: string, newChildren: DocTree["children"]) => {
          if (node.path === targetPath) {
            // 找到目标节点，更新其子节点
            node.children = newChildren
            // 移除加载标记
            delete node.has_children
            return true
          }
          
          // 递归查找
          if (node.children) {
            for (const child of node.children) {
              if (updateNode(child, targetPath, newChildren)) {
                return true
              }
            }
          }
          
          return false
        }
        
        // 更新文档树
        if (this.docTree) {
          updateNode(this.docTree, path, subtree.children)
        }
        
      } catch (err) {
        console.error(`Error loading subtree for path ${path}:`, err)
      } finally {
        // 更新加载状态
        this.subTreeLoading[path] = false
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