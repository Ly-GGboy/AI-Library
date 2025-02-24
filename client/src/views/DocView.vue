<template>
  <div class="doc-view">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <ol class="breadcrumb-list">
        <li class="breadcrumb-item">
          <router-link to="/" class="breadcrumb-link">
            <HomeIcon class="breadcrumb-icon" />
            首页
          </router-link>
        </li>
        <li
          v-for="(item, index) in breadcrumb"
          :key="item.path"
          class="breadcrumb-item"
        >
          <ChevronRightIcon class="breadcrumb-separator" />
          <span
            v-if="index === breadcrumb.length - 1"
            class="breadcrumb-current"
          >
            {{ item.name }}
          </span>
          <router-link
            v-else
            :to="{ name: 'home', hash: `#${item.path}` }"
            class="breadcrumb-link"
          >
            {{ item.name }}
          </router-link>
        </li>
      </ol>
    </nav>

    <main class="main">
      <aside class="sidebar">
        <DocTree />
      </aside>

      <article class="article">
        <ImmersiveReader>
          <div v-if="loading" class="loading">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          </div>
          <div v-else-if="error" class="error">
            {{ error }}
          </div>
          <div v-else-if="currentDoc">
            <MarkdownViewer 
              v-if="!isPDFDoc" 
              :content="currentDoc.content || ''" 
              :loading="loading" 
              :error="error"
            />
            <PDFViewer 
              v-else
              :path="currentDoc.path"
            />
          </div>
          <div v-else class="no-content">
            未找到文档内容
          </div>
        </ImmersiveReader>
        
        <div v-if="currentDoc && !isPDFDoc" class="doc-navigation">
          <router-link
            v-if="prevDoc"
            :to="{ name: 'doc', params: { path: prevDoc.path } }"
            class="prev-link"
          >
            <ChevronLeftIcon class="w-5 h-5" />
            <span>{{ prevDoc.name }}</span>
          </router-link>
          <router-link
            v-if="nextDoc"
            :to="{ name: 'doc', params: { path: nextDoc.path } }"
            class="next-link"
          >
            <span>{{ nextDoc.name }}</span>
            <ChevronRightIcon class="w-5 h-5" />
          </router-link>
        </div>
      </article>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocStore } from '../stores/doc'
import { HomeIcon, ChevronRightIcon, ChevronLeftIcon } from '@heroicons/vue/24/outline'
import DocTree from '../components/DocTree.vue'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import PDFViewer from '../components/PDFViewer.vue'
import ImmersiveReader from '../components/ImmersiveReader.vue'
import { storeToRefs } from 'pinia'
import type { DocContent } from '../services/api'

const route = useRoute()
const router = useRouter()
const docStore = useDocStore()
const { currentDoc, loading, error, docTree } = storeToRefs(docStore)

// 计算面包屑
const breadcrumb = computed(() => {
  if (!currentDoc.value?.path) return []
  const parts = currentDoc.value.path.split('/')
  return parts.map((part, index) => ({
    name: part,
    path: parts.slice(0, index + 1).join('/')
  }))
})

// 判断当前文档是否为PDF
const isPDFDoc = computed(() => {
  return currentDoc.value?.name ? currentDoc.value.name.toLowerCase().endsWith('.pdf') : false
})

// 修改loadContent函数
const loadContent = async () => {
  const path = route.params.path as string
  console.log('DocView: Loading content for path:', path)
  if (path) {
    try {
      docStore.$patch({ loading: true, error: null })
      
      if (path.toLowerCase().endsWith('.pdf')) {
        // PDF 文件不需要加载内容，直接设置当前文档路径
        const pdfDoc: DocContent = {
          path,
          name: path.split('/').pop() || '',
          content: '',
          last_modified: new Date().toISOString()
        }
        docStore.$patch({
          currentDoc: pdfDoc,
          loading: false,
          error: null
        })
      } else {
        await docStore.loadDocContent(path)
      }
      console.log('DocView: Content loaded, currentDoc:', currentDoc.value)
    } catch (err) {
      console.error('Error loading content:', err)
      docStore.$patch({ 
        error: err instanceof Error ? err.message : '加载文档失败',
        loading: false 
      })
    }
  }
}

// 优化查找当前文档在文档树中的位置的函数
const findCurrentDocPosition = () => {
  if (!docTree.value || !currentDoc.value) {
    console.log('findCurrentDocPosition: docTree or currentDoc is null', {
      docTree: docTree.value,
      currentDoc: currentDoc.value
    })
    return []
  }
  
  // 打印完整的文档树结构
  console.log('Document Tree Structure:', JSON.stringify(docTree.value, null, 2))
  console.log('Current Doc Path:', currentDoc.value.path)
  
  const normalizedCurrentPath = currentDoc.value.path.replace(/\\/g, '/')
  console.log('Normalized Current Path:', normalizedCurrentPath)
  
  interface TreeNode {
    name?: string
    type?: string
    path?: string
    children?: TreeNode[]
    items?: TreeNode[]
  }

  interface TreePosition {
    node: TreeNode
    index: number
  }

  const findInTree = (
    node: TreeNode,
    parent: TreePosition[] = [],
    level: number = 0
  ): TreePosition[] | null => {
    if (!node) return null
    
    const indent = '  '.repeat(level)
    const nodePath = node.path?.replace(/\\/g, '/')
    const nodeName = node.name || ''
    
    console.log(`${indent}Checking node:`, {
      name: nodeName,
      type: node.type,
      path: nodePath,
      hasChildren: !!node.children?.length,
      childrenCount: node.children?.length || 0,
      hasItems: !!node.items?.length,
      itemsCount: node.items?.length || 0,
      level
    })
    
    // 如果是文件且路径匹配（放宽匹配条件）
    const isMatch = nodePath === normalizedCurrentPath || 
                   (node.type !== 'dir' && nodeName && normalizedCurrentPath.endsWith(nodeName))
    
    if (isMatch) {
      console.log(`${indent}Found matching file:`, {
        path: nodePath,
        name: nodeName,
        level,
        parentChain: parent.map(p => p.node.name)
      })
      
      return [
        ...parent,
        { 
          node,
          index: parent.length > 0 ? parent[parent.length - 1].index : 0
        }
      ]
    }
    
    // 递归搜索所有可能的子节点
    const searchChildren = (items: TreeNode[], itemType: string) => {
      for (let i = 0; i < items.length; i++) {
        const child = items[i]
        console.log(`${indent}Searching ${itemType} [${i}]:`, child.name || 'unnamed')
        
        const result = findInTree(
          child,
          [...parent, { node, index: i }],
          level + 1
        )
        
        if (result) {
          console.log(`${indent}Found result in ${itemType}:`, {
            childName: child.name || 'unnamed',
            index: i,
            level: level + 1
          })
          return result
        }
      }
      return null
    }
    
    // 搜索 children
    if (node.children?.length) {
      const result = searchChildren(node.children, 'children')
      if (result) return result
    }
    
    // 搜索 items
    if (node.items?.length) {
      const result = searchChildren(node.items, 'items')
      if (result) return result
    }
    
    return null
  }
  
  const result = findInTree(docTree.value)
  console.log('Search result:', {
    found: !!result,
    resultLength: result?.length || 0,
    path: result ? result[result.length - 1]?.node?.path : null,
    chain: result ? result.map(p => ({ name: p.node.name, index: p.index })) : []
  })
  
  return result || []
}

// 优化导航计算逻辑
const navigation = computed(() => {
  const position = findCurrentDocPosition()
  console.log('Navigation: starting with position:', {
    positionLength: position.length,
    positionChain: position.map(p => ({
      name: p.node.name || 'unnamed',
      index: p.index
    }))
  })
  
  if (!position.length) {
    console.log('Navigation: no position found, returning null')
    return { prevDoc: null, nextDoc: null }
  }

  const findPrevDoc = (node: any, level: number = 0): any => {
    if (!node) return null
    
    const indent = '  '.repeat(level)
    console.log(`${indent}Finding prev doc for:`, {
      name: node.name || 'unnamed',
      type: node.type,
      path: node.path,
      level
    })
    
    // 如果是文件，直接返回
    if (node.type !== 'dir') {
      console.log(`${indent}Found file node:`, node.path)
      return node
    }
    
    const items = node.children || node.items
    if (items?.length) {
      console.log(`${indent}Searching in ${items.length} children/items`)
      return findPrevDoc(items[items.length - 1], level + 1)
    }
    
    return null
  }

  const findNextDoc = (node: any, level: number = 0): any => {
    if (!node) return null
    
    const indent = '  '.repeat(level)
    console.log(`${indent}Finding next doc for:`, {
      name: node.name || 'unnamed',
      type: node.type,
      path: node.path,
      level
    })
    
    // 如果是文件，直接返回
    if (node.type !== 'dir') {
      console.log(`${indent}Found file node:`, node.path)
      return node
    }
    
    const items = node.children || node.items
    if (items?.length) {
      console.log(`${indent}Searching in ${items.length} children/items`)
      return findNextDoc(items[0], level + 1)
    }
    
    return null
  }

  const findSiblingDoc = (parentNode: any, currentIndex: number, direction: 'prev' | 'next'): any => {
    const items = parentNode?.children || parentNode?.items
    
    console.log('Finding sibling doc:', {
      parentName: parentNode?.name || 'unnamed',
      currentIndex,
      direction,
      itemsCount: items?.length || 0
    })
    
    if (!items?.length) {
      console.log('No children/items in parent node')
      return null
    }
    
    const siblingIndex = direction === 'prev' ? currentIndex - 1 : currentIndex + 1
    console.log('Looking for sibling:', {
      direction,
      siblingIndex,
      maxIndex: items.length - 1
    })
    
    if (siblingIndex < 0 || siblingIndex >= items.length) {
      console.log('Sibling index out of bounds')
      return null
    }
    
    const sibling = items[siblingIndex]
    if (!sibling) {
      console.log('No sibling found')
      return null
    }
    
    console.log('Found sibling:', {
      name: sibling.name || 'unnamed',
      type: sibling.type,
      path: sibling.path
    })
    
    return direction === 'prev' ? findPrevDoc(sibling) : findNextDoc(sibling)
  }

  // 获取当前文档的父节点和索引
  const lastPosition = position[position.length - 1]
  const parentPosition = position[position.length - 2]
  
  const parentNode = parentPosition?.node || docTree.value
  const currentIndex = lastPosition?.index

  console.log('Current position info:', {
    currentPath: currentDoc.value?.path,
    parentName: parentNode?.name || 'root',
    currentIndex,
    positionLength: position.length,
    parentChildren: parentNode?.children?.map(c => c.name || 'unnamed') || []
  })

  // 查找上一篇和下一篇
  const prevDoc = findSiblingDoc(parentNode, currentIndex, 'prev')
  const nextDoc = findSiblingDoc(parentNode, currentIndex, 'next')

  console.log('Found navigation docs:', {
    prev: prevDoc?.path,
    next: nextDoc?.path,
    prevName: prevDoc?.name,
    nextName: nextDoc?.name
  })

  return { prevDoc, nextDoc }
})

const prevDoc = computed(() => navigation.value.prevDoc)
const nextDoc = computed(() => navigation.value.nextDoc)

// 添加导航处理函数
const handleNavigate = (path: string) => {
  router.push({ name: 'doc', params: { path } })
}

onMounted(loadContent)

watch(() => route.params.path, async (path) => {
  if (path) {
    try {
      if (path.toString().toLowerCase().endsWith('.pdf')) {
        // PDF 文件不需要加载内容，直接设置当前文档路径
        docStore.$patch({
          currentDoc: { path: path.toString(), name: path.toString().split('/').pop() || '' },
          loading: false,
          error: null
        })
      } else {
        await docStore.loadDocContent(path.toString())
      }
    } catch (err) {
      console.error('Error loading document:', err)
    }
  }
}, { immediate: true })
</script>

<style scoped>
.doc-view {
  @apply min-h-screen bg-gray-50 dark:bg-gray-900;
}

.breadcrumb {
  @apply bg-white shadow-sm py-2 px-6 sticky top-0 z-10 dark:bg-gray-800;
  height: 3rem;
}

.breadcrumb-list {
  @apply flex items-center max-w-[1200px] mx-auto h-full;
}

.breadcrumb-item {
  @apply flex items-center;
}

.breadcrumb-link {
  @apply flex items-center text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-50;
}

.breadcrumb-current {
  @apply text-gray-900 dark:text-gray-50;
}

.breadcrumb-icon {
  @apply w-5 h-5 mr-1;
}

.breadcrumb-separator {
  @apply w-5 h-5 text-gray-400 mx-2 dark:text-gray-500;
}

.main {
  @apply flex relative max-w-[1200px] mx-auto;
  min-height: calc(100vh - 3rem);
}

.sidebar {
  @apply w-64 flex-shrink-0 bg-white shadow-lg fixed h-[calc(100vh-3rem)] overflow-y-auto 
    dark:bg-gray-800 dark:border-gray-700;
  left: max(0px, calc(50% - 600px));
  top: 3rem;
}

.article {
  @apply flex-grow bg-white w-0 dark:bg-gray-800;
  margin-left: calc(max(0px, calc(50% - 600px)) + 256px);
  width: calc(min(1200px, 100%) - 256px);
  padding-top: 3rem;
}

.doc-navigation {
  @apply flex justify-between mt-8 px-6 pb-6 border-t pt-6 
    border-gray-200 dark:border-gray-700;
}

.prev-link, .next-link {
  @apply flex items-center gap-4 text-gray-600 hover:text-gray-900 transition-colors max-w-[45%]
    dark:text-gray-400 dark:hover:text-gray-50;
}

.nav-placeholder {
  @apply w-[45%];
}

.nav-icon {
  @apply w-5 h-5 flex-shrink-0;
}

.nav-content {
  @apply flex flex-col;
}

.nav-label {
  @apply text-sm text-gray-500 dark:text-gray-500;
}

.nav-title {
  @apply text-base font-medium truncate dark:text-gray-300;
}

.prev {
  @apply text-left;
}

.next {
  @apply text-right;
}

/* 添加响应式布局 */
@media (max-width: 1200px) {
  .main {
    @apply px-0;
  }
  
  .sidebar {
    @apply fixed left-0 z-20;
    transform: translateX(-100%);
    transition: transform 0.3s ease-in-out;
  }
  
  .sidebar.active {
    transform: translateX(0);
  }
  
  .article {
    @apply ml-0;
    width: 100%;
  }
}

.loading {
  @apply flex justify-center items-center min-h-[200px];
}

.error {
  @apply text-red-500 p-4 text-center;
}

.no-content {
  @apply text-gray-500 p-4 text-center;
}

/* 调整全局控制栏位置 */
:global(.global-controls) {
  top: 4rem !important;
}
</style>