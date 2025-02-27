<template>
  <div class="home dark:bg-gray-900">
    <header class="header dark:bg-gray-800">
      <div class="header-content">
        <h1 class="title dark:text-gray-100">文档中心</h1>
        <a 
          href="https://frp6.mmszxc.xin:18925" 
          target="_blank" 
          class="backup-link"
          title="访问速度不佳可访问此地址"
        >
          备用地址
        </a>
        <div class="header-actions">
          <AnnouncementButton 
            @click="openAnnouncementBoard" 
            :has-new-updates="hasNewUpdates" 
            class="mr-2"
          />
          <button
            @click="toggleTheme"
            @mouseenter="themeButtonHover = true"
            @mouseleave="themeButtonHover = false"
            class="theme-toggle"
            :title="isDark ? '切换到亮色模式' : '切换到暗色模式'"
          >
            <Transition name="icon-switch" mode="out-in">
              <SunIcon v-if="isDark" key="sun" class="w-5 h-5 text-gray-400 dark:text-gray-400" />
              <MoonIcon v-else key="moon" class="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </Transition>
          </button>
        </div>
      </div>
      <SearchBar class="search" />
    </header>

    <main class="main">
      <aside class="sidebar dark:bg-gray-800">
        <DocTree />
      </aside>

      <div class="content dark:bg-gray-800">
        <div v-if="loading" class="loading">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        </div>
        <div v-else-if="error" class="error dark:bg-red-900 dark:text-red-100">
          {{ error }}
        </div>
        <div v-else class="recent-docs">
          <h2 class="section-title dark:text-gray-100">最近更新</h2>
          <ul v-if="recentDocs.length > 0" class="doc-list">
            <li v-for="doc in recentDocs" :key="doc.path" class="doc-item dark:hover:bg-gray-700">
              <router-link
                :to="{ name: 'doc', params: { path: doc.path } }"
                class="doc-link"
              >
                <DocumentTextIcon class="doc-icon dark:text-gray-500" />
                <div class="doc-info">
                  <span class="doc-name dark:text-gray-100">{{ doc.name.replace('.md', '') }}</span>
                  <span class="doc-date dark:text-gray-500">{{ formatDate(doc.last_modified) }}</span>
                </div>
              </router-link>
            </li>
          </ul>
          <div v-else class="empty dark:text-gray-400">
            暂无最近更新的文档
          </div>
        </div>
      </div>
    </main>

    <AnnouncementBoard ref="announcementBoardRef" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocStore } from '../stores/doc'
import { useThemeStore } from '../stores/theme'
import { useAnnouncementStore } from '../stores/announcement'
import { DocumentTextIcon, SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import SearchBar from '../components/SearchBar.vue'
import DocTree from '../components/DocTree.vue'
import AnnouncementButton from '../components/announcement/AnnouncementButton.vue'
import AnnouncementBoard from '../components/announcement/AnnouncementBoard.vue'
import { storeToRefs } from 'pinia'
import type { DocTree as DocTreeType } from '../services/api'
import type { ComponentPublicInstance } from 'vue'

const route = useRoute()
const router = useRouter()
const docStore = useDocStore()
const themeStore = useThemeStore()
const announcementStore = useAnnouncementStore()
const { recentDocs, loading, error, docTree } = storeToRefs(docStore)
const { isDark } = storeToRefs(themeStore)
const { toggleTheme } = themeStore
const { hasNewUpdates } = storeToRefs(announcementStore)
const themeButtonHover = ref(false)

const announcementBoardRef = ref<ComponentPublicInstance & { openBoard: () => void } | null>(null)

const openAnnouncementBoard = () => {
  if (announcementBoardRef.value) {
    announcementBoardRef.value.openBoard()
    announcementStore.markUpdatesAsViewed()
  }
}

onMounted(async () => {
  await docStore.loadDocTree()  // 先加载文档树
  await docStore.loadRecentDocs()
  
  // 加载更新信息
  try {
    await announcementStore.getUpdates()
  } catch (err) {
    console.error('Failed to load updates:', err)
  }
  
  // 如果有 hash，跳转到对应的目录
  if (route.hash) {
    const path = route.hash.slice(1) // 移除 # 符号
    const node = docTree.value && findNodeByPath(docTree.value, path)
    if (node) {
      // 展开对应的目录
      const storageKey = `tree-node-${path}`
      localStorage.setItem(storageKey, 'true')
    }
  }
})

// 监听 hash 变化
watch(() => route.hash, (newHash) => {
  if (newHash) {
    const path = newHash.slice(1)
    const node = docTree.value && findNodeByPath(docTree.value, path)
    if (node) {
      // 展开对应的目录
      const storageKey = `tree-node-${path}`
      localStorage.setItem(storageKey, 'true')
    }
  }
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 递归查找节点
const findNodeByPath = (node: DocTreeType, path: string): DocTreeType | null => {
  if (!node) return null
  if (node.path === path) return node
  if (node.children) {
    for (const child of node.children) {
      const found = findNodeByPath(child, path)
      if (found) return found
    }
  }
  return null
}
</script>

<style scoped>
.home {
  @apply min-h-screen bg-gray-50;
}

.header {
  @apply bg-white shadow dark:bg-gray-800 sticky top-0 z-30 py-4 px-6 flex flex-col relative;
}

.header-content {
  @apply flex items-center justify-between mb-4 relative;
  min-height: 40px; /* 确保有足够的高度 */
}

.title {
  @apply text-2xl font-bold text-gray-900;
}

.backup-link {
  @apply ml-4 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300;
  @apply px-3 py-1 rounded-full bg-primary-50 hover:bg-primary-100 dark:bg-primary-900/30 dark:hover:bg-primary-900/40;
  @apply transition-colors duration-200;
}

.header-actions {
  @apply flex items-center gap-2 z-[95] ml-auto;
  position: relative;
}

.theme-toggle, .announcement-button {
  @apply p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors;
  position: relative;
  z-index: 95;
  transform-origin: center;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.theme-toggle:hover, .announcement-button:hover {
  transform: scale(1.1);
}

.theme-toggle:active, .announcement-button:active {
  transform: scale(0.95);
}

.search {
  @apply max-w-2xl;
}

.main {
  @apply container mx-auto px-4 py-6 flex gap-6;
}

.sidebar {
  @apply w-64 flex-shrink-0 bg-white rounded-lg shadow;
}

.content {
  @apply flex-grow bg-white rounded-lg shadow p-6;
}

.section-title {
  @apply text-lg font-semibold text-gray-900 mb-4;
}

.doc-list {
  @apply space-y-2;
}

.doc-item {
  @apply rounded-lg hover:bg-gray-50 transition-colors;
}

.doc-link {
  @apply flex items-center gap-3 p-3;
}

.doc-icon {
  @apply w-5 h-5 text-gray-400;
}

.doc-info {
  @apply flex flex-col;
}

.doc-name {
  @apply text-gray-900;
}

.doc-date {
  @apply text-sm text-gray-500;
}

.loading {
  @apply flex justify-center items-center py-8;
}

.error {
  @apply text-red-500 p-4 rounded bg-red-50 my-4;
}

.empty {
  @apply text-gray-500 text-center py-8;
}

.mr-2 {
  display: block;
}

/* 图标切换动画 */
.icon-switch-enter-active,
.icon-switch-leave-active {
  transition: all 0.2s ease;
}

.icon-switch-enter-from,
.icon-switch-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(15deg);
}
</style> 