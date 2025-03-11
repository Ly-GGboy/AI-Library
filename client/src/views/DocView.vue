<template>
  <div class="doc-view min-h-screen bg-white dark:bg-gray-900">
    <!-- 顶部导航栏 -->
    <header class="glass sticky top-0 z-50 border-b border-gray-100 dark:border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center h-16">
          <!-- 面包屑导航 -->
          <nav class="flex items-center space-x-2 text-sm" aria-label="Breadcrumb">
            <router-link to="/" class="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors">
              <HomeIcon class="w-5 h-5" />
            </router-link>
            <span class="text-gray-400 dark:text-gray-600">/</span>
            <template v-for="(item, index) in breadcrumb" :key="item.path">
              <router-link
                v-if="index !== breadcrumb.length - 1"
                :to="{ name: 'home', hash: `#${item.path}` }"
                class="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 transition-colors"
              >
                {{ item.name }}
              </router-link>
              <span
                v-else
                class="text-gray-700 dark:text-gray-300 font-medium"
              >
                {{ item.name }}
              </span>
              <span v-if="index !== breadcrumb.length - 1" class="text-gray-400 dark:text-gray-600">/</span>
            </template>
          </nav>
          
          <div class="flex-1"></div>
          
  
        </div>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="flex">
      <!-- 左侧边栏 -->
      <aside class="w-64 border-r border-gray-100 dark:border-gray-800 h-[calc(100vh-4rem)] overflow-y-auto">
        <!-- 搜索框 -->
        <div class="p-4 border-b border-gray-100 dark:border-gray-800">
          <div class="relative">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索文章..." 
              class="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 border-none focus:outline-none focus:ring-2 focus:ring-gray-200 dark:focus:ring-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 text-sm transition-all"
            >
            <button class="absolute right-3 top-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300">
              <MagnifyingGlassIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
        
        <!-- 最近访问 -->
        <div class="p-4 border-b border-gray-100 dark:border-gray-800">
          <h3 class="text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">最近访问</h3>
          <RecentDocs />
        </div>

        <!-- 文档导航树 -->
        <div class="p-4">
          <DocTree :load-data="true" :filter="searchQuery" />
        </div>
      </aside>

      <!-- 右侧内容区 -->
      <main class="flex-1 h-[calc(100vh-4rem)] overflow-y-auto">
        <div class="max-w-5xl mx-auto px-8 py-12">
          <div v-if="loading" class="loading flex justify-center items-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
          </div>
          <div v-else-if="error" class="error text-red-500 dark:text-red-400 p-4 rounded bg-red-50 dark:bg-red-900/20">
            {{ error }}
          </div>
          <div v-else-if="currentDoc" class="zoom-container" :style="zoomStyles">
            <MarkdownViewer 
              v-if="!isPDFDoc" 
              :content="currentDoc.content || ''" 
              :loading="loading" 
              :error="error"
              class="prose prose-lg max-w-none dark:prose-invert"
            />
            <PDFViewer 
              v-else
              :path="currentDoc.path"
              class="w-full"
            />
            
            <!-- 文档导航 -->
            <div v-if="!isPDFDoc" class="doc-navigation mt-8 flex justify-between items-center">
              <router-link
                v-if="prevDoc"
                :to="{ name: 'doc', params: { path: prevDoc.path } }"
                class="flex items-center space-x-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                <ChevronLeftIcon class="w-5 h-5" />
                <span>{{ prevDoc.name }}</span>
              </router-link>
              <router-link
                v-if="nextDoc"
                :to="{ name: 'doc', params: { path: nextDoc.path } }"
                class="flex items-center space-x-2 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                <span>{{ nextDoc.name }}</span>
                <ChevronRightIcon class="w-5 h-5" />
              </router-link>
            </div>
          </div>
          <div v-else class="text-gray-500 dark:text-gray-400 text-center py-8">
            未找到文档内容
          </div>
        </div>
      </main>
    </div>

    <!-- 悬浮工具栏 -->
    <div class="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-white dark:bg-gray-800 rounded-full shadow-lg px-4 py-2 flex items-center space-x-4 z-50">
      <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400">
        <Bars3Icon class="w-5 h-5" />
      </button>
      <div class="h-4 border-r border-gray-200 dark:border-gray-700"></div>
      <button 
        @click="zoomOut"
        class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
        :disabled="zoomLevel <= 0.5"
      >
        <MagnifyingGlassMinusIcon class="w-5 h-5" />
      </button>
      <span class="text-sm text-gray-700 dark:text-gray-300">{{ Math.round(zoomLevel * 100) }}%</span>
      <button 
        @click="zoomIn"
        class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
        :disabled="zoomLevel >= 2"
      >
        <MagnifyingGlassPlusIcon class="w-5 h-5" />
      </button>
      <div class="h-4 border-r border-gray-200 dark:border-gray-700"></div>
      <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400">
        <ShareIcon class="w-5 h-5" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocStore } from '../stores/doc'
import { 
  HomeIcon, 
  ChevronRightIcon, 
  ChevronLeftIcon,
  MagnifyingGlassIcon,
  MagnifyingGlassMinusIcon,
  MagnifyingGlassPlusIcon,
  Bars3Icon,
  ShareIcon
} from '@heroicons/vue/24/outline'
import DocTree from '../components/DocTree.vue'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import PDFViewer from '../components/PDFViewer.vue'
import RecentDocs from '../components/RecentDocs.vue'
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

// 初始化加载
onMounted(async () => {
  // 确保文档树已加载
  if (!docTree.value) {
    await docStore.loadDocTree()
  }
})

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

// 优化 watch，使用 immediate 确保首次加载
watch(() => route.params.path, async (path) => {
  if (path) {
    await loadContent()
  }
}, { immediate: true })

const searchQuery = ref('')

// 修改缩放相关的实现
const zoomLevel = ref(1)
const ZOOM_STEP = 0.1
const MIN_ZOOM = 0.5
const MAX_ZOOM = 2

// 计算缩放样式
const zoomStyles = computed(() => {
  const scale = zoomLevel.value
  return {
    width: `${100 / scale}%`,  // 调整容器宽度以适应缩放
    transform: `scale(${scale})`,
    transformOrigin: 'top left',
    marginBottom: `${(scale - 1) * 100}px`, // 补偿缩放导致的高度变化
  }
})

const zoomIn = () => {
  if (zoomLevel.value < MAX_ZOOM) {
    zoomLevel.value = Math.min(MAX_ZOOM, zoomLevel.value + ZOOM_STEP)
  }
}

const zoomOut = () => {
  if (zoomLevel.value > MIN_ZOOM) {
    zoomLevel.value = Math.max(MIN_ZOOM, zoomLevel.value - ZOOM_STEP)
  }
}
</script>

<style scoped>
/* 毛玻璃效果 */
.glass {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dark .glass {
  background: rgba(31, 41, 55, 0.8);
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}
.dark ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}
.dark ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 文档内容样式 */
:deep(.prose) {
  max-width: none;
}

:deep(.prose pre) {
  background-color: #f8f9fa;
  border-radius: 0.5rem;
  padding: 1rem;
  margin: 1.5rem 0;
}

.dark :deep(.prose pre) {
  background-color: #1f2937;
}

:deep(.prose img) {
  border-radius: 0.5rem;
  margin: 1.5rem 0;
}

:deep(.prose h1) {
  font-size: 2.5rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.2;
  margin-bottom: 1.5rem;
}

:deep(.prose h2) {
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.025em;
  margin: 2rem 0 1rem;
}

:deep(.prose h3) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1.5rem 0 0.75rem;
}

:deep(.prose p) {
  font-size: 1.125rem;
  line-height: 1.7;
  margin-bottom: 1.25rem;
}

/* 添加缩放容器样式 */
.zoom-container {
  position: relative;
  transform-origin: top left;
}

/* 修改滚动条样式，确保在缩放时仍然可见 */
main {
  overflow-y: auto;
  overflow-x: hidden;
}
</style>