<template>
  <div class="markdown-viewer">
    <div v-if="loading" class="loading">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else ref="markdownBodyRef" class="markdown-body" v-html="renderedContent"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick, ref } from 'vue'
import { marked } from 'marked'
import Prism from 'prismjs'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import { useRoute } from 'vue-router'

// API 基础 URL 配置 - 使用相对路径
const API_BASE_URL = ''  // 空字符串表示使用相对路径

const props = defineProps<{
  content?: string | null
  loading?: boolean
  error?: string | null
}>()

const route = useRoute()
const markdownBodyRef = ref<HTMLElement | null>(null)

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

  // 始终返回 img 标签，不再检查文件扩展名
  return `<img src="${href}" alt="${text}"${title ? ` title="${title}"` : ''} class="markdown-image" loading="lazy">`
}

const renderedContent = computed(() => {
  try {
    if (!props.content) {
      return ''
    }

    // 预处理 Markdown 内容
    let processedContent = props.content
    
    // 处理相对路径
    const basePath = getBasePath()
    
    if (basePath) {
      // 替换图片路径 - 修改正则表达式以匹配更多格式
      processedContent = processedContent.replace(
        /!\[(.*?)\]\((.*?)\)/g,  // 修改正则以匹配所有图片语法
        (match, alt, path) => {
          // 如果路径已经是完整URL或API路径，直接使用
          if (path.startsWith('http') || path.startsWith('/api/')) {
            return match
          }
          // 处理相对路径
          const imagePath = path.startsWith('images/') 
            ? `${basePath}${path}`
            : `${basePath}${path}`
          const encodedPath = imagePath.split('/').map(part => encodeURIComponent(part)).join('/')
          return `![${alt}](/api/docs/content/${encodedPath})`
        }
      )
      
      // 替换链接路径
      processedContent = processedContent.replace(
        /(?<!!)\[([^\]]+)\]\((?!http|\/api)(.*?)\)/g,  // 修改正则以排除图片语法
        (match, text, path) => {
          return `[${text}](/api/docs/content/${basePath}${path})`
        }
      )
    }

    // 扩展marked选项，改进代码块渲染
    const markedOptions = {
      gfm: true,
      breaks: true,
      renderer,
      pedantic: false,
      highlight: function(code: string, lang: string) {
        // 保留language-xxxx类名，让Prism能够识别语言
        if (lang && Prism.languages[lang]) {
          try {
            return `<pre class="language-${lang}"><code class="language-${lang}">${Prism.highlight(code, Prism.languages[lang], lang)}</code></pre>`;
          } catch (err) {
            console.error('Prism highlighting error:', err);
          }
        }
        
        // 无法识别语言时，使用普通代码块
        return `<pre><code>${code}</code></pre>`;
      }
    };

    // 使用marked处理Markdown
    const html = marked(processedContent, markedOptions);
    
    return html;
  } catch (error) {
    console.error('Error rendering markdown:', error)
    return '<div class="error">Error rendering content</div>'
  }
})

// 监听内容变化并优化代码高亮
watch(() => props.content, () => {
  nextTick(() => {
    try {
      // 找到容器元素
      const container = markdownBodyRef.value;
      if (!container) return;
      
      // 只处理没有语言类的代码块，因为有语言类的已经在marked渲染时处理过了
      const unlabeledCodeBlocks = container.querySelectorAll('pre code:not([class*="language-"])');
      if (unlabeledCodeBlocks.length > 0) {
        unlabeledCodeBlocks.forEach((block) => {
          // 尝试检测语言
          const text = block.textContent || '';
          // 根据内容尝试猜测语言
          let detectedLang = '';
          
          // 简单启发式检测
          if (text.includes('function') && text.includes('{') && text.includes('}')) {
            detectedLang = 'javascript';
          } else if (text.includes('def ') && text.includes(':')) {
            detectedLang = 'python';
          } else if (text.includes('class ') && text.includes('{') && text.includes('public')) {
            detectedLang = 'java';
          } else if (text.includes('import ') && text.includes('from ')) {
            detectedLang = 'python';
          }
          
          // 如果检测到可能的语言，设置类并高亮
          if (detectedLang && Prism.languages[detectedLang]) {
            block.className = `language-${detectedLang}`;
            Prism.highlightElement(block);
          }
        });
      }
    } catch (error) {
      console.error('Error highlighting unlabeled code blocks:', error)
    }
  })
}, { immediate: true })

onMounted(() => {
  // 初次加载时可能需要处理未识别语言的代码块
  nextTick(() => {
    if (markdownBodyRef.value) {
      const unlabeledCodeBlocks = markdownBodyRef.value.querySelectorAll('pre code:not([class*="language-"])');
      if (unlabeledCodeBlocks.length > 0) {
        unlabeledCodeBlocks.forEach((block) => {
          // 使用通用样式高亮
          Prism.highlightElement(block);
        });
      }
    }
  });
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
  @apply bg-gray-100 text-gray-800 p-4 rounded-lg dark:bg-gray-900 dark:text-white;
  max-width: 100%;
  overflow-x: auto;
}

:deep(.markdown-body code) {
  @apply font-mono text-sm text-gray-800 bg-gray-100 dark:text-gray-300 dark:bg-gray-800;
}

:deep(.markdown-body pre code) {
  @apply bg-transparent;
  background-color: transparent !important;
  color: inherit !important;
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

<!-- Add custom Prism syntax highlighting styles -->
<style>
/* Prism syntax highlighting for light/dark mode */
/* Token styling for light mode */
.token.comment,
.token.prolog,
.token.doctype,
.token.cdata {
  color: #5e6e77;
}

.token.punctuation {
  color: #5F6368;
}

.token.property,
.token.tag,
.token.boolean,
.token.number,
.token.constant,
.token.symbol,
.token.deleted {
  color: #e3116c;
}

.token.selector,
.token.attr-name,
.token.string,
.token.char,
.token.builtin,
.token.inserted {
  color: #067d17;
}

.token.operator,
.token.entity,
.token.url,
.language-css .token.string,
.style .token.string {
  color: #a67f59;
}

.token.atrule,
.token.attr-value,
.token.keyword {
  color: #0b51c1;
}

.token.function,
.token.class-name {
  color: #c18401;
}

.token.regex,
.token.important,
.token.variable {
  color: #e90;
}

/* Dark mode overrides */
.dark .token.comment,
.dark .token.prolog,
.dark .token.doctype,
.dark .token.cdata {
  color: #8292a2;
}

.dark .token.punctuation {
  color: #9EACB9;
}

.dark .token.property,
.dark .token.tag,
.dark .token.boolean,
.dark .token.number,
.dark .token.constant,
.dark .token.symbol,
.dark .token.deleted {
  color: #ff79c6;
}

.dark .token.selector,
.dark .token.attr-name,
.dark .token.string,
.dark .token.char,
.dark .token.builtin,
.dark .token.inserted {
  color: #50fa7b;
}

.dark .token.operator,
.dark .token.entity,
.dark .token.url,
.dark .language-css .token.string,
.dark .style .token.string {
  color: #f1fa8c;
}

.dark .token.atrule,
.dark .token.attr-value,
.dark .token.keyword {
  color: #8be9fd;
}

.dark .token.function,
.dark .token.class-name {
  color: #bd93f9;
}

.dark .token.regex,
.dark .token.important,
.dark .token.variable {
  color: #ffb86c;
}
</style> 