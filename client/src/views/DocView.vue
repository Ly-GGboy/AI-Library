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
      <button
        class="theme-toggle"
        @click="themeStore.toggleTheme"
        :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
      >
        <SunIcon v-if="isDark" class="theme-icon" />
        <MoonIcon v-else class="theme-icon" />
      </button>
    </nav>

    <main class="main">
      <aside class="sidebar">
        <DocTree />
      </aside>

      <article class="article">
        <template v-if="isPDF">
          <PDFViewer
            :path="route.params.path as string"
            :loading="loading"
            :error="error"
          />
        </template>
        <template v-else>
          <MarkdownViewer
            :content="currentDoc?.content || ''"
            :loading="loading"
            :error="error"
          />
        </template>
        
        <div class="doc-navigation">
          <router-link
            v-if="prevDoc"
            :to="{ name: 'doc', params: { path: prevDoc.path } }"
            class="nav-link prev"
          >
            <ChevronLeftIcon class="nav-icon" />
            <div class="nav-content">
              <span class="nav-label">上一篇</span>
              <span class="nav-title">{{ prevDoc.name }}</span>
            </div>
          </router-link>
          <div v-else class="nav-placeholder"></div>

          <router-link
            v-if="nextDoc"
            :to="{ name: 'doc', params: { path: nextDoc.path } }"
            class="nav-link next"
          >
            <div class="nav-content">
              <span class="nav-label">下一篇</span>
              <span class="nav-title">{{ nextDoc.name }}</span>
            </div>
            <ChevronRightIcon class="nav-icon" />
          </router-link>
          <div v-else class="nav-placeholder"></div>
        </div>
      </article>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDocStore } from '../stores/doc'
import { useThemeStore } from '../stores/theme'
import { HomeIcon, ChevronRightIcon, ChevronLeftIcon, SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import DocTree from '../components/DocTree.vue'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import PDFViewer from '../components/PDFViewer.vue'
import { storeToRefs } from 'pinia'

const route = useRoute()
const docStore = useDocStore()
const themeStore = useThemeStore()
const { currentDoc, breadcrumb, loading, error, docTree } = storeToRefs(docStore)
const { isDark } = storeToRefs(themeStore)

const loadContent = async () => {
  const path = route.params.path as string
  console.log('DocView: Loading content for path:', path)
  if (path) {
    await docStore.loadDocContent(path)
    console.log('DocView: Content loaded, currentDoc:', currentDoc.value)
  }
}

// 查找当前文档在文档树中的位置
const findCurrentDocPosition = () => {
  if (!docTree.value || !currentDoc.value) return []
  
  const findInTree = (node: any, parent: any[] = []): any[] | null => {
    if (!node) return null
    if (node.path === currentDoc.value?.path) {
      return parent
    }
    if (node.children) {
      for (let i = 0; i < node.children.length; i++) {
        const result = findInTree(node.children[i], [...parent, { node: node.children[i], index: i }])
        if (result) return result
      }
    }
    return null
  }
  
  const result = findInTree(docTree.value)
  return result || []
}

// 计算上一篇和下一篇文档
const navigation = computed(() => {
  const position = findCurrentDocPosition()
  if (!position || position.length === 0) return { prevDoc: null, nextDoc: null }
  
  const lastItem = position[position.length - 1]
  if (!lastItem) return { prevDoc: null, nextDoc: null }
  
  const parentNode = position.length > 1 ? position[position.length - 2].node : docTree.value
  if (!parentNode || !parentNode.children) return { prevDoc: null, nextDoc: null }
  
  let prev = null
  let next = null
  
  // 查找上一篇
  if (lastItem.index > 0) {
    // 在同级查找上一篇
    let prevNode = parentNode.children[lastItem.index - 1]
    // 如果上一个是目录，找其最后一个文档
    while (prevNode && prevNode.children && prevNode.children.length > 0) {
      prevNode = prevNode.children[prevNode.children.length - 1]
    }
    if (prevNode && prevNode.type === 'file') prev = prevNode
  }
  
  // 查找下一篇
  if (lastItem.index < parentNode.children.length - 1) {
    // 在同级查找下一篇
    let nextNode = parentNode.children[lastItem.index + 1]
    // 如果下一个是目录，找其第一个文档
    while (nextNode && nextNode.children && nextNode.children.length > 0) {
      nextNode = nextNode.children[0]
    }
    if (nextNode && nextNode.type === 'file') next = nextNode
  }
  
  return {
    prevDoc: prev,
    nextDoc: next
  }
})

const prevDoc = computed(() => navigation.value.prevDoc)
const nextDoc = computed(() => navigation.value.nextDoc)

// 判断当前文档是否为PDF
const isPDF = computed(() => {
  const path = route.params.path as string
  return path.toLowerCase().endsWith('.pdf')
})

onMounted(loadContent)

watch(() => route.params.path, loadContent)
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

.theme-toggle {
  @apply fixed right-4 top-2 p-2 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 
    dark:text-gray-400 dark:hover:text-gray-50 dark:hover:bg-gray-700 transition-colors;
}

.theme-icon {
  @apply w-5 h-5;
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
}

.doc-navigation {
  @apply flex justify-between mt-8 px-6 pb-6 border-t pt-6 
    border-gray-200 dark:border-gray-700;
}

.nav-link {
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
</style>