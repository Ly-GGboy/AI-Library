<template>
  <div class="tree-node" v-show="isVisible">
    <template v-if="node.name === 'root'">
      <div v-for="child in node.children" :key="child.path || child.name">
        <TreeNode :node="child" :filter="filter" @select="$emit('select')" />
      </div>
    </template>
    <template v-else>
      <div
        v-if="node.children && node.children.length > 0"
        class="node-content folder"
        @click="toggleExpand"
      >
        <component
          :is="expanded ? 'ChevronDownIcon' : 'ChevronRightIcon'"
          class="w-4 h-4 text-gray-400 flex-shrink-0"
        />
        <FolderIcon v-if="!expanded" class="w-4 h-4 text-gray-500 flex-shrink-0" />
        <FolderOpenIcon v-else class="w-4 h-4 text-primary-500 flex-shrink-0" />
        <div class="node-name-container">
          <span 
            class="node-name folder-name" 
            :class="{ 'expanded': isNameExpanded }"
            :title="!isNameExpanded ? node.name : ''"
          >
            {{ displayName }}
          </span>
          <button 
            v-if="needsExpansion"
            class="expand-button"
            @click="toggleNameExpand"
            :title="isNameExpanded ? '收起' : '展开'"
          >
            <component
              :is="isNameExpanded ? 'ChevronDoubleUpIcon' : 'ChevronDoubleDownIcon'"
              class="w-3 h-3"
            />
          </button>
        </div>
      </div>
      <router-link
        v-else-if="node.type === 'file' && node.path"
        :to="{ name: 'doc', params: { path: node.path } }"
        class="node-content article"
        :class="{ 'active': isActive }"
        ref="activeLink"
        @click="$emit('select')"
      >
        <DocumentTextIcon class="w-4 h-4 flex-shrink-0" :class="isActive ? 'text-primary-500' : 'text-gray-400'" />
        <div class="node-name-container">
          <span 
            class="node-name article-name" 
            :class="{ 
              'text-primary-600 font-medium': isActive,
              'expanded': isNameExpanded 
            }"
            :title="!isNameExpanded ? node.name.replace('.md', '') : ''"
          >
            {{ displayName }}
          </span>
          <button 
            v-if="needsExpansion"
            class="expand-button"
            @click="toggleNameExpand"
            :title="isNameExpanded ? '收起' : '展开'"
          >
            <component
              :is="isNameExpanded ? 'ChevronDoubleUpIcon' : 'ChevronDoubleDownIcon'"
              class="w-3 h-3"
            />
          </button>
        </div>
      </router-link>
      <div v-else class="node-content">
        <DocumentIcon class="w-4 h-4 text-gray-400 flex-shrink-0" />
        <div class="node-name-container">
          <span 
            class="node-name" 
            :class="{ 'expanded': isNameExpanded }"
            :title="!isNameExpanded ? node.name : ''"
          >
            {{ displayName }}
          </span>
          <button 
            v-if="needsExpansion"
            class="expand-button"
            @click="toggleNameExpand"
            :title="isNameExpanded ? '收起' : '展开'"
          >
            <component
              :is="isNameExpanded ? 'ChevronDoubleUpIcon' : 'ChevronDoubleDownIcon'"
              class="w-3 h-3"
            />
          </button>
        </div>
      </div>

      <div v-if="expanded && node.children" class="node-children">
        <TreeNode
          v-for="child in node.children"
          :key="child.path || child.name"
          :node="{ ...child, parent: node }"
          :filter="filter"
          @select="$emit('select')"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import type { DocTree } from '../services/api'
import {
  ChevronRightIcon,
  ChevronDownIcon,
  DocumentTextIcon,
  DocumentIcon,
  FolderIcon,
  FolderOpenIcon,
  ChevronDoubleDownIcon,
  ChevronDoubleUpIcon
} from '@heroicons/vue/24/outline'
import { useRoute } from 'vue-router'

const props = defineProps<{
  node: DocTree
  filter?: string
}>()

const emit = defineEmits<{
  (e: 'select'): void
}>()

const route = useRoute()
const activeLink = ref<HTMLElement | null>(null)

// 使用节点路径作为唯一标识
const nodeKey = props.node.path || props.node.name
const storageKey = `tree-node-${nodeKey}`

// 从 localStorage 获取初始展开状态
const expanded = ref(localStorage.getItem(storageKey) === 'true')

// 计算当前节点是否被选中
const isActive = computed(() => {
  if (!props.node.path) return false
  return route.params.path === props.node.path
})

// 检查节点是否是活动路径的一部分
const isPartOfActivePath = computed(() => {
  if (!route.params.path) return false
  return isNodePartOfPath(props.node, route.params.path as string)
})

// 递归检查节点是否是指定路径的一部分
const isNodePartOfPath = (node: DocTree, targetPath: string): boolean => {
  if (node.path === targetPath) return true
  if (node.children) {
    return node.children.some(child => isNodePartOfPath(child, targetPath))
  }
  return false
}

// 检查节点是否匹配搜索条件
const isVisible = computed(() => {
  if (!props.filter) return true
  if (props.node.name === 'root') return true
  
  const searchText = props.filter.toLowerCase()
  const nodeName = props.node.name.toLowerCase()
  
  // 如果是文件夹，检查是否有子节点匹配
  if (props.node.children) {
    return nodeName.includes(searchText) || hasMatchingChild(props.node, searchText)
  }
  
  // 如果是文件，直接检查名称
  return nodeName.includes(searchText)
})

// 递归检查是否有匹配的子节点
const hasMatchingChild = (node: DocTree, searchText: string): boolean => {
  if (!node.children) return false
  return node.children.some(child => {
    const childName = child.name.toLowerCase()
    if (childName.includes(searchText)) return true
    return hasMatchingChild(child, searchText)
  })
}

// 监听搜索条件变化
watch(() => props.filter, (newFilter) => {
  if (newFilter && hasMatchingChild(props.node, newFilter.toLowerCase())) {
    expanded.value = true
  } else if (!newFilter) {
    // 恢复到之前的展开状态
    expanded.value = localStorage.getItem(storageKey) === 'true'
  }
})

const toggleExpand = () => {
  expanded.value = !expanded.value
  // 保存展开状态到 localStorage
  localStorage.setItem(storageKey, expanded.value.toString())
}

// 清除所有展开状态
const clearAllExpanded = () => {
  const keys = Object.keys(localStorage)
  keys.forEach(key => {
    if (key.startsWith('tree-node-')) {
      localStorage.removeItem(key)
    }
  })
}

// 滚动到选中的文章
const scrollToActive = async () => {
  await nextTick()
  if (isActive.value && activeLink.value) {
    // 等待一下确保 DOM 完全更新
    setTimeout(() => {
      const container = document.querySelector('.tree-container')
      if (container && activeLink.value) {
        const elementTop = activeLink.value.offsetTop
        container.scrollTo({
          top: elementTop - 20, // 留出一点顶部空间
          behavior: 'smooth'
        })
      }
    }, 100)
  }
}

// 监听路由变化
watch(() => route.params.path, async (newPath) => {
  if (newPath) {
    // 清除所有展开状态
    clearAllExpanded()
    // 如果当前节点是路径的一部分，展开它
    if (isPartOfActivePath.value) {
      expanded.value = true
      localStorage.setItem(storageKey, 'true')
      // 如果是当前选中的文章，滚动到它的位置
      if (isActive.value) {
        await scrollToActive()
      }
    } else {
      expanded.value = false
      localStorage.removeItem(storageKey)
    }
  }
}, { immediate: true })

// 初始化展开状态和滚动位置
onMounted(async () => {
  if (isPartOfActivePath.value) {
    expanded.value = true
    localStorage.setItem(storageKey, 'true')
    if (isActive.value) {
      await scrollToActive()
    }
  } else {
    expanded.value = false
    localStorage.removeItem(storageKey)
  }
})

// 添加展开状态控制
const isNameExpanded = ref(false)

// 检查标题是否过长需要展开
const needsExpansion = computed(() => {
  const maxLength = 30 // 可以根据实际需求调整
  return props.node.name.length > maxLength
})

// 获取显示的标题文本
const displayName = computed(() => {
  if (props.node.type === 'file') {
    const name = props.node.name.replace('.md', '')
    return isNameExpanded.value ? name : name
  }
  return isNameExpanded.value ? props.node.name : props.node.name
})

// 切换标题展开状态
const toggleNameExpand = (event: Event) => {
  if (needsExpansion.value) {
    event.stopPropagation()
    isNameExpanded.value = !isNameExpanded.value
  }
}
</script>

<style scoped>
.tree-node {
  @apply text-sm;
}

/* 确保父容器可以滚动 */
:deep(.tree-container) {
  @apply overflow-y-auto h-[calc(100vh-4rem)];
  scroll-behavior: smooth;
}

.node-content {
  @apply flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer 
    transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800
    active:scale-[0.98] touch-pan-y;
  min-width: 0; /* 确保flex容器可以正确处理溢出 */
}

.node-content.folder {
  @apply hover:bg-gray-50 dark:hover:bg-gray-800;
}

.node-content.article {
  @apply hover:bg-gray-100 ml-2 dark:hover:bg-gray-800;
}

.node-content.active {
  @apply bg-primary-50 hover:bg-primary-100
    dark:bg-primary-900/30 dark:hover:bg-primary-900/40;
}

.node-name {
  @apply text-gray-700 dark:text-gray-300 min-w-0 flex-1 cursor-default
    whitespace-normal break-words leading-relaxed;
  word-break: break-word;
}

.folder-name {
  @apply font-medium text-gray-600 dark:text-gray-300 cursor-pointer;
}

.article-name {
  @apply text-gray-500 dark:text-gray-400 cursor-pointer;
}

.node-children {
  @apply pl-4 border-l border-gray-100 ml-2 my-0.5
    dark:border-gray-700;
}

/* 添加hover效果 */
.node-name:hover {
  @apply text-gray-900 dark:text-gray-100;
}

/* 优化文本溢出显示 */
.node-content {
  @apply flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer 
    transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800
    active:scale-[0.98] touch-pan-y;
  min-width: 0; /* 确保flex容器可以正确处理溢出 */
}

/* 确保文本容器可以正确处理溢出 */
.node-content > div,
.node-content > a {
  @apply min-w-0 flex-1;
}

/* 移动端优化 */
@media (max-width: 767px) {
  .node-content {
    @apply py-2.5 px-3;
  }

  .node-children {
    @apply pl-3 ml-1;
  }
}

.node-name-container {
  @apply flex items-center min-w-0 flex-1;
  max-width: 300px; /* 调整最大宽度 */
}

.node-name {
  @apply text-gray-700 dark:text-gray-300 min-w-0 flex-1 cursor-default
    whitespace-normal break-words leading-relaxed;
  word-break: break-word;
}

.node-name.expanded {
  /* 展开后换行显示 */
  @apply whitespace-normal break-words;
  word-break: break-word;
}

.expand-button {
  display: none;
}

.folder-name {
  @apply font-medium text-gray-600 dark:text-gray-300 cursor-pointer;
}

.article-name {
  @apply text-gray-500 dark:text-gray-400 cursor-pointer;
}

/* 优化展开后的间距 */
.node-content {
  @apply flex items-start gap-2 px-2 py-1.5 rounded cursor-pointer 
    transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800
    active:scale-[0.98] touch-pan-y;
  min-width: 0;
}

.node-content.folder {
  @apply hover:bg-gray-50 dark:hover:bg-gray-800;
}

.node-content.article {
  @apply hover:bg-gray-100 ml-2 dark:hover:bg-gray-800;
}

/* 图标垂直对齐 */
.node-content > :first-child {
  @apply mt-1;
}
</style> 