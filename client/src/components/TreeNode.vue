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
        class="node-content folder group"
        @click="toggleExpand"
      >
        <component
          :is="expanded ? 'ChevronDownIcon' : 'ChevronRightIcon'"
          class="w-4 h-4 text-gray-400 flex-shrink-0 mr-1"
        />
        <FolderIcon v-if="!expanded" class="w-4 h-4 text-blue-400 flex-shrink-0 mr-1 group-hover:text-blue-500" />
        <FolderOpenIcon v-else class="w-4 h-4 text-blue-500 flex-shrink-0 mr-1" />
        <div class="node-name-container">
          <span 
            class="node-name folder-name" 
            :class="{ 'expanded': isNameExpanded, 'font-medium text-blue-700': expanded }"
            :title="!isNameExpanded ? node.name : ''"
          >
            {{ displayName }}
          </span>
          <span 
            class="count-badge" 
            v-if="articleCount > 0"
            :title="`${articleCount} ${props.node.type === 'file' ? '节' : '篇'}`"
          >
            {{ articleCount }}
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
        v-else-if="node.path"
        :to="{ name: 'doc', params: { path: node.path } }"
        class="node-content article"
        :class="{ 'active': isActive }"
        :title="node.path"
        ref="activeLink"
        @click="$emit('select')"
      >
        <DocumentTextIcon class="w-4 h-4 flex-shrink-0 mr-1" :class="isActive ? 'text-blue-500' : 'text-gray-400'" />
        <div class="node-name-container">
          <span 
            class="node-name article-name" 
            :class="{ 
              'text-blue-700 font-medium': isActive,
              'expanded': isNameExpanded 
            }"
            :title="!isNameExpanded ? node.name.replace('.md', '') : ''"
          >
            {{ displayName }}
          </span>
          <span 
            class="count-badge" 
            v-if="articleCount > 0"
            :title="`${articleCount} ${props.node.type === 'file' ? '节' : '篇'}`"
          >
            {{ articleCount }}
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
        <DocumentIcon class="w-4 h-4 text-gray-400 flex-shrink-0 mr-1" />
        <div class="node-name-container">
          <span 
            class="node-name" 
            :class="{ 'expanded': isNameExpanded }"
            :title="!isNameExpanded ? node.name : ''"
          >
            {{ displayName }}
          </span>
          <span 
            class="count-badge" 
            v-if="articleCount > 0"
            :title="`${articleCount} ${props.node.type === 'file' ? '节' : '篇'}`"
          >
            {{ articleCount }}
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

      <div v-if="expanded && node.children" :class="['node-children', getIndentClass]">
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
import type { PropType } from 'vue'
import { useRoute } from 'vue-router'
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

interface TreeNodeType {
  name: string
  path: string
  type: 'dir' | 'file'
  children?: TreeNodeType[]
  items?: TreeNodeType[]
  parent?: TreeNodeType
}

const props = defineProps({
  node: {
    type: Object as PropType<TreeNodeType>,
    required: true
  },
  filter: {
    type: String,
    default: ''
  }
})

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
const isNodePartOfPath = (node: TreeNodeType, targetPath: string): boolean => {
  if (node.path === targetPath) return true
  if (node.children) {
    return node.children.some(child => isNodePartOfPath(child, targetPath))
  }
  return false
}

// 递归检查节点及其子节点是否匹配搜索条件
const hasMatchingNode = (node: TreeNodeType, searchTerm: string): boolean => {
  // 检查当前节点名称是否匹配
  if (node.name.toLowerCase().includes(searchTerm)) {
    return true
  }
  
  // 递归检查所有子节点
  if (node.children) {
    return node.children.some(child => hasMatchingNode(child, searchTerm))
  }
  
  return false
}

// 添加计算属性来处理过滤
const isVisible = computed(() => {
  if (!props.filter) return true
  
  const searchTerm = props.filter.toLowerCase()
  
  // 检查当前节点及其所有子节点是否匹配
  return hasMatchingNode(props.node, searchTerm)
})

// 监听搜索条件变化
watch(() => props.filter, (newFilter) => {
  if (newFilter) {
    // 如果当前节点或其子节点匹配搜索条件，则展开
    if (isVisible.value) {
      expanded.value = true
    }
  } else {
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

// 修改计算缩进的函数，使用动态递减的缩进值
const getNodeLevel = (node: TreeNodeType): number => {
  let level = 0;
  let current = node;
  while (current.parent) {
    level++;
    current = current.parent;
  }
  return level;
}

const getIndentClass = computed(() => {
  const level = getNodeLevel(props.node);
  return `indent-level-${Math.min(level, 5)}`; // 最多支持5级缩进
});

// 修改计算文章和章节数的函数
const isArticleFile = (name: string | undefined): boolean => {
  return Boolean(name && (name.endsWith('.md') || name.endsWith('.pdf')));
}

const getArticleCount = (node: TreeNodeType): number => {
  if (!node.children) return 0;
  return node.children.reduce((count, child) => {
    if (isArticleFile(child.name)) {
      return count + 1;
    }
    return count + getArticleCount(child);
  }, 0);
}

const getSectionCount = (node: TreeNodeType): number => {
  if (!node.children) return 0;
  // 计算直接子节点中的markdown和pdf文件数量
  return node.children.filter((child: TreeNodeType) => isArticleFile(child.name)).length;
}

// 修改计算属性
const articleCount = computed(() => {
  // 如果是文件夹，显示其下的文章文件总数
  if (props.node.children) {
    return getArticleCount(props.node);
  }
  // 如果是文章文件，显示其子章节数
  if (isArticleFile(props.node.name)) {
    return getSectionCount(props.node);
  }
  return 0;
});
</script>

<style scoped>
.tree-node {
  @apply text-sm;
}

/* 修改滚动容器的样式 */
:deep(.tree-container) {
  @apply overflow-y-auto;
  height: 100%; /* 改用100%高度而不是固定高度 */
  scroll-behavior: smooth;
  position: sticky; /* 添加sticky定位 */
  top: 0;
}

/* 确保内容容器可以正确滚动 */
.node-content {
  @apply flex items-center gap-1 px-1 py-2.5 text-sm rounded-lg cursor-pointer 
    transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800
    active:scale-[0.98] touch-pan-y relative; /* 添加relative定位 */
  min-width: 0;
}

.node-content.folder {
  @apply hover:bg-gray-50 dark:hover:bg-gray-800;
}

.node-content.article {
  @apply hover:bg-gray-50 dark:hover:bg-gray-800 ml-0;
}

.node-content.active {
  @apply bg-blue-50 hover:bg-blue-100
    dark:bg-blue-900/30 dark:hover:bg-blue-900/40;
}

.node-name {
  @apply text-gray-700 dark:text-gray-300 min-w-0 flex-1 cursor-default
    whitespace-nowrap overflow-hidden text-ellipsis;
  max-width: calc(100% - 30px); /* 为计数徽章留出空间 */
}

.folder-name {
  @apply font-medium text-gray-700 dark:text-gray-300 cursor-pointer;
}

.article-name {
  @apply text-gray-700 dark:text-gray-400 cursor-pointer;
}

.node-children {
  @apply ml-3 my-1;
}

/* 添加hover效果 */
.node-name:hover {
  @apply text-gray-900 dark:text-gray-100;
}

.node-name-container {
  @apply flex items-center min-w-0 flex-1 gap-1;
  max-width: 100%; /* 允许容器使用全部可用宽度 */
  position: relative; /* 添加relative定位 */
  z-index: 1; /* 确保内容在滚动时保持可见 */
}

.node-name.expanded {
  @apply whitespace-normal break-words;
  word-break: break-word;
}

.expand-button {
  display: none;
}

/* 优化展开后的间距 */
.node-content {
  @apply flex items-center gap-1 px-1 py-2.5 text-sm rounded-lg cursor-pointer 
    transition-all duration-200 hover:bg-gray-50 dark:hover:bg-gray-800
    active:scale-[0.98] touch-pan-y;
  min-width: 0;
}

.count-badge {
  @apply text-[11px] leading-[16px] px-1.5 rounded-full bg-gray-100 text-gray-500 ml-auto flex-shrink-0 
    dark:bg-gray-800/60 dark:text-gray-400 min-w-[20px] h-[20px] inline-flex items-center justify-center;
  font-feature-settings: "tnum";
}

.node-content:hover .count-badge {
  @apply bg-gray-200 dark:bg-gray-700/60;
}

.node-content.active .count-badge {
  @apply bg-blue-100/70 text-blue-600
    dark:bg-blue-900/30 dark:text-blue-400;
}
</style> 