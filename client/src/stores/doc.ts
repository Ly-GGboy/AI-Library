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
      console.log(`开始加载子树: ${path}`);
      
      try {
        const subtree = await docApi.getDocSubtree(path)
        console.log(`子树加载成功: ${path}, 子节点数: ${subtree?.children?.length || 0}`);
        
        // 递归函数查找目标节点
        const updateNode = (node: DocTree, targetPath: string, newChildren: DocTree["children"]) => {
          if (node.path === targetPath) {
            // 找到目标节点，更新其子节点
            console.log(`找到目标节点: ${targetPath}, 更新子节点数: ${newChildren?.length || 0}`);
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
          const updated = updateNode(this.docTree, path, subtree.children)
          if (!updated) {
            console.warn(`未找到目标节点 ${path} 来更新子树`);
          }
        } else {
          console.warn(`文档树为空，无法更新子树 ${path}`);
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