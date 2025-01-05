<template>
  <div class="markdown-viewer">
    <div v-if="loading" class="loading">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else class="markdown-body" v-html="renderedContent"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import Prism from 'prismjs'
import 'prismjs/themes/prism-tomorrow.css'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import { useRoute } from 'vue-router'

// API 基础 URL 配置 - 使用相对路径
const API_BASE_URL = ''  // 空字符串表示使用相对路径

const props = defineProps<{
  content: string
  loading?: boolean
  error?: string | null
}>()

const route = useRoute()

// 获取当前文档的基础路径
const getBasePath = () => {
  const path = route.params.path as string
  return path ? path.substring(0, path.lastIndexOf('/') + 1) : ''
}

// 创建自定义渲染器
const renderer = new marked.Renderer()

// 重写图片渲染方法
renderer.image = (href: string, title: string, text: string) => {
  // 如果已经是完整的 URL，直接使用
  if (href && href.startsWith('http')) {
    // do nothing
  }
  // 如果是 API 路径，使用相对路径
  else if (href && href.startsWith('/api/')) {
    href = href  // 直接使用相对路径
  }
  // 如果是相对路径，添加基础路径
  else if (href && !href.startsWith('/')) {
    const basePath = getBasePath()
    // 获取图片所在目录的路径
    const imagePath = href.startsWith('images/') 
      ? `${basePath}${href}`  // 直接拼接，不再重复添加 images/
      : `${basePath}${href}`
    // 对路径进行 URL 编码，但保留斜杠
    const encodedPath = imagePath.split('/').map(part => encodeURIComponent(part)).join('/')
    href = `/api/docs/content/${encodedPath}`  // 使用相对路径
  }
  return `<img src="${href}" alt="${text}"${title ? ` title="${title}"` : ''} class="markdown-image" loading="lazy">`
}

const renderedContent = computed(() => {
  console.log('MarkdownViewer content:', props.content)
  if (!props.content) {
    console.log('No content to render')
    return ''
  }
  const html = marked(props.content, {
    gfm: true,
    breaks: true,
    renderer
  })
  console.log('Rendered HTML:', html)
  return html
})

watch(renderedContent, () => {
  nextTick(() => {
    Prism.highlightAll()
  })
})

onMounted(() => {
  Prism.highlightAll()
})
</script>

<style scoped>
.markdown-viewer {
  @apply p-6;
  max-width: 100%;
  overflow-x: hidden;
}

.loading {
  @apply flex justify-center items-center py-8;
}

.error {
  @apply text-red-500 p-4 rounded bg-red-50 my-4 dark:bg-red-900/20;
}

:deep(.markdown-body) {
  @apply prose prose-slate max-w-none dark:prose-invert dark:text-gray-300;
  width: 100%;
}

:deep(.markdown-body pre) {
  @apply bg-gray-800 text-white p-4 rounded-lg dark:bg-gray-900;
  max-width: 100%;
  overflow-x: auto;
}

:deep(.markdown-body code) {
  @apply font-mono text-sm dark:text-gray-300;
}

:deep(.markdown-body img) {
  @apply rounded-lg shadow-lg my-4 dark:shadow-gray-900;
  max-width: 100%;
  height: auto;
  display: inline-block;
}

:deep(.markdown-body a) {
  @apply text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300;
}

:deep(.markdown-body blockquote) {
  @apply border-l-4 border-gray-200 dark:border-gray-700;
}

:deep(.markdown-body table) {
  @apply border-collapse border border-gray-200 dark:border-gray-700;
}

:deep(.markdown-body th) {
  @apply bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700;
}

:deep(.markdown-body td) {
  @apply border border-gray-200 dark:border-gray-700;
}

/* 优化图片容器布局 */
:deep(.markdown-body p) {
  @apply my-4;
  max-width: 100%;
}

/* 添加响应式布局 */
@media (max-width: 768px) {
  .markdown-viewer {
    @apply px-4;
  }
}
</style> 