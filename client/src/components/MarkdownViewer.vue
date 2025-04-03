<template>
  <div class="markdown-viewer">
    <div v-if="loading" class="loading">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    </div>
    <div v-else-if="error" class="error">
      {{ error }}
    </div>
    <div v-else ref="markdownBodyRef" class="markdown-body" v-html="renderedContent"></div>
    
    <!-- 图片查看器 -->
    <Teleport to="body" v-if="showImageViewer">
      <div class="image-viewer" @click="closeImageViewer">
        <button class="image-viewer-close" @click.stop="closeImageViewer">&times;</button>
        
        <div class="image-viewer-content" @click.stop>
          <img 
            :src="activeImageSrc" 
            class="image-viewer-img" 
            :style="{ transform: `scale(${zoomLevel})` }"
            alt="Enlarged image" 
          />
        </div>
        
        <!-- 缩放控制 -->
        <div class="image-viewer-controls" @click.stop>
          <button class="control-btn" @click="zoomOut" title="缩小">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
          </button>
          <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
          <button class="control-btn" @click="zoomIn" title="放大">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line><line x1="11" y1="8" x2="11" y2="14"></line><line x1="8" y1="11" x2="14" y2="11"></line></svg>
          </button>
          <button class="control-btn" @click="resetZoom" title="重置">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path><path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path><path d="M16 21h5v-5"></path></svg>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick, ref, onUnmounted } from 'vue'
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

// 图片查看器状态
const showImageViewer = ref(false)
const activeImageSrc = ref('')
const zoomLevel = ref(1) // 缩放级别

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

  // 生成低质量的占位符URL（使用较小的尺寸）
  const placeholderUrl = href.includes('?') ? 
    `${href}&w=20&q=10` : 
    `${href}?w=20&q=10`;

  // 返回增强的图片标签，不包含文件名显示
  return `
    <figure class="image-container">
      <img 
        class="markdown-image lazyload" 
        data-src="${href}" 
        alt="${text}" 
        ${title ? ` title="${title}"` : ''} 
        loading="lazy"
        data-error="false"
        onload="this.classList.add('loaded'); this.parentElement.classList.add('loaded'); window.dispatchEvent(new Event('scroll')); window.dispatchEvent(new CustomEvent('update-progress', {bubbles: true}));"
        onerror="this.classList.add('error'); this.parentElement.classList.add('error'); this.dataset.error='true'; this.setAttribute('src', '/error-placeholder.svg')"
      />
      <div class="image-placeholder">
        <div class="loading-spinner"></div>
      </div>
      <div class="image-error-message">图片加载失败</div>
    </figure>
  `
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
      
      // 内容变化时重新初始化懒加载
      initLazyLoading();
      
      // 立即触发更新，不使用延迟
      dispatchScrollEvent();
    } catch (error) {
      console.error('Error handling content update:', error)
    }
  })
}, { immediate: true })

// 创建防抖函数
const debounce = (fn: Function, delay: number) => {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return function(...args: any[]) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fn(...args);
      timer = null;
    }, delay);
  };
};

// 触发滚动事件以更新进度条
const dispatchScrollEvent = () => {
  // 使用更高优先级的方式触发滚动事件
  try {
    // 创建自定义事件，强制更新进度条
    const updateEvent = new CustomEvent('update-progress', { bubbles: true });
    window.dispatchEvent(updateEvent);
    
    // 同时触发滚动事件以保证兼容性
    const scrollEvent = new Event('scroll', { bubbles: true });
    window.dispatchEvent(scrollEvent);
    
    // 针对主容器触发事件
    const mainContent = document.querySelector('main');
    if (mainContent) {
      mainContent.dispatchEvent(scrollEvent);
      mainContent.dispatchEvent(updateEvent);
    }
    
    // 针对markdown容器触发事件
    if (markdownBodyRef.value) {
      markdownBodyRef.value.dispatchEvent(scrollEvent);
      markdownBodyRef.value.dispatchEvent(updateEvent);
    }
  } catch (error) {
    console.error('Error dispatching scroll events:', error);
  }
}

onMounted(() => {
  // 初次加载时高亮处理
  nextTick(() => {
    if (markdownBodyRef.value) {
      const unlabeledCodeBlocks = markdownBodyRef.value.querySelectorAll('pre code:not([class*="language-"])');
      if (unlabeledCodeBlocks.length > 0) {
        unlabeledCodeBlocks.forEach((block) => {
          // 使用通用样式高亮
          Prism.highlightElement(block);
        });
      }
      
      // 初始化图片懒加载
      initLazyLoading();
      
      // 立即触发更新，不使用延迟
      dispatchScrollEvent();
    }
  });
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyDown);
  
  // 添加对自定义事件的监听
  window.addEventListener('update-progress', () => {
    // 自定义事件触发时直接调用进度条更新功能
    const updateProgressEvent = new CustomEvent('update-progress-bar');
    window.dispatchEvent(updateProgressEvent);
  });
  
  // 添加滚动事件监听 - 实时触发而非防抖
  const handleScroll = () => {
    // 检查是否有新的图片进入可视区域
    if (lazyImageObserver) {
      checkVisibleImages();
    }
    // 直接触发更新
    const updateProgressEvent = new CustomEvent('update-progress-bar');
    window.dispatchEvent(updateProgressEvent);
  };
  
  window.addEventListener('scroll', handleScroll, { passive: true });
  
  // 监听DOM变化，自动触发更新
  if ('MutationObserver' in window) {
    const observer = new MutationObserver((mutations) => {
      // 当DOM变化时触发更新
      dispatchScrollEvent();
    });
    
    // 监视文档内容变化
    if (markdownBodyRef.value) {
      observer.observe(markdownBodyRef.value, {
        childList: true, 
        subtree: true
      });
    }
  }
})

// IntersectionObserver实例
let lazyImageObserver: IntersectionObserver | null = null;

// 检查可见区域内的图片
const checkVisibleImages = () => {
  if (!markdownBodyRef.value) return;
  
  // 获取所有尚未加载的懒加载图片
  const unloadedImages = markdownBodyRef.value.querySelectorAll('img.lazyload:not(.visible)');
  if (unloadedImages.length === 0) return;
  
  // 检查每个图片是否在可视区域内
  unloadedImages.forEach(img => {
    const rect = img.getBoundingClientRect();
    const isVisible = 
      rect.top >= -300 && 
      rect.left >= 0 && 
      rect.bottom <= (window.innerHeight + 300) && 
      rect.right <= window.innerWidth;
    
    // 如果图片在可视区域内，加载它
    if (isVisible) {
      const image = img as HTMLImageElement;
      if (image.dataset.src) {
        image.src = image.dataset.src;
        image.classList.add('visible');
        
        // 图片加载完成后触发滚动事件更新进度条
        image.onload = () => {
          dispatchScrollEvent();
        };
      }
    }
  });
};

// 组件卸载时移除事件监听
const handleKeyDown = (e: KeyboardEvent) => {
  if (!showImageViewer.value) return;
  
  switch (e.key) {
    case 'Escape':
      closeImageViewer();
      break;
    case '+':
    case '=': // 等号键通常与加号键在同一位置
      zoomIn();
      e.preventDefault();
      break;
    case '-':
    case '_': // 下划线键通常与减号键在同一位置
      zoomOut();
      e.preventDefault();
      break;
    case '0':
      resetZoom();
      e.preventDefault();
      break;
  }
}

// 实现图片懒加载
const initLazyLoading = () => {
  if (!markdownBodyRef.value) return;
  
  // 检查浏览器是否支持 IntersectionObserver
  if ('IntersectionObserver' in window) {
    // 如果已有观察者实例，先断开连接
    if (lazyImageObserver) {
      lazyImageObserver.disconnect();
    }
    
    // 创建新的观察者实例
    lazyImageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const lazyImage = entry.target as HTMLImageElement;
          if (lazyImage.dataset.src) {
            lazyImage.src = lazyImage.dataset.src;
            lazyImage.classList.add('visible');
            observer.unobserve(lazyImage);
            
            // 图片加载完成后触发滚动事件更新进度条
            lazyImage.onload = () => {
              dispatchScrollEvent();
            };
          }
        }
      });
    }, {
      rootMargin: '200px 0px', // 提前200px开始加载
      threshold: 0.01 // 只要有1%可见就开始加载
    });
    
    // 获取所有懒加载图片并观察它们
    const lazyImages = markdownBodyRef.value.querySelectorAll('img.lazyload');
    lazyImages.forEach(image => {
      if (lazyImageObserver) {
        lazyImageObserver.observe(image);
      }
    });
  } else {
    // 不支持 IntersectionObserver 的浏览器上，直接加载所有图片
    const lazyImages = markdownBodyRef.value.querySelectorAll('img.lazyload');
    lazyImages.forEach(image => {
      const img = image as HTMLImageElement;
      if (img.dataset.src) {
        img.src = img.dataset.src;
        img.classList.add('visible');
        
        // 图片加载完成后触发滚动事件更新进度条
        img.onload = () => {
          dispatchScrollEvent();
        };
      }
    });
  }
  
  // 添加图片点击放大事件
  setupImageViewer();
}

// 设置图片查看器
const setupImageViewer = () => {
  if (!markdownBodyRef.value) return;
  
  // 获取所有图片
  const images = markdownBodyRef.value.querySelectorAll('.markdown-image');
  
  // 为每个图片添加点击事件
  images.forEach(img => {
    img.addEventListener('click', (e) => {
      e.preventDefault(); // 阻止默认行为
      e.stopPropagation(); // 阻止事件冒泡
      
      const image = e.target as HTMLImageElement;
      if (image.dataset.error === 'true') return; // 不处理加载失败的图片
      
      // 优先使用data-src属性，这是原始图片路径
      let imgSrc = image.dataset.src || '';
      
      // 如果没有data-src，则使用src属性
      if (!imgSrc && image.src) {
        imgSrc = image.src;
      }
      
      // 确保有图片路径
      if (imgSrc) {
        console.log('Opening image in viewer:', imgSrc);
        showImageInViewer(imgSrc);
      } else {
        console.error('No image source found for clicked image');
      }
    });
    
    // 添加可点击的视觉提示
    img.classList.add('clickable');
  });
}

// 在查看器中显示图片
const showImageInViewer = (src: string) => {
  // 移除可能添加的查询参数（如 ?w=20&q=10 这种用于占位符的缩略图参数）
  const cleanSrc = src.split('?')[0];
  
  // 设置查看器图片源
  activeImageSrc.value = cleanSrc;
  
  // 禁止背景滚动
  const originalStyle = {
    overflow: document.body.style.overflow,
    paddingRight: document.body.style.paddingRight
  };
  
  // 计算滚动条宽度，防止页面跳动
  const scrollBarWidth = window.innerWidth - document.documentElement.clientWidth;
  
  // 记录当前滚动位置
  const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
  
  // 使页面不可滚动但看起来仍然在原位置
  document.body.style.overflow = 'hidden';
  document.body.style.paddingRight = `${scrollBarWidth}px`;
  
  // 激活查看器
  showImageViewer.value = true;
  
  // 存储这些状态，以便关闭时恢复
  return { originalStyle, scrollPosition };
}

// 关闭图片查看器
const closeImageViewer = () => {
  // 隐藏查看器
  showImageViewer.value = false;
  
  // 重置缩放级别
  zoomLevel.value = 1;
  
  // 恢复原始样式
  document.body.style.overflow = '';
  document.body.style.paddingRight = '';
  
  // 立即触发更新，不使用延迟
  dispatchScrollEvent();
}

// 缩放控制函数
const zoomIn = () => {
  if (zoomLevel.value < 3) {  // 最大放大3倍
    zoomLevel.value += 0.25
  }
}

const zoomOut = () => {
  if (zoomLevel.value > 0.5) {  // 最小缩小到0.5倍
    zoomLevel.value -= 0.25
  }
}

const resetZoom = () => {
  zoomLevel.value = 1
}

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('scroll', checkVisibleImages);
  if (lazyImageObserver) {
    lazyImageObserver.disconnect();
  }
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
  display: block;
  margin: 1em auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

/* 懒加载图片容器样式 */
:deep(.image-container) {
  @apply relative my-6 rounded-lg overflow-hidden;
  width: 100%;
  max-width: 100%;
  transition: transform 0.3s ease;
}

:deep(.image-container:hover) {
  transform: translateY(-2px);
}

:deep(.markdown-image) {
  @apply rounded-lg shadow-lg;
  opacity: 0;
  width: 100%;
  max-width: 100%;
  height: auto;
  display: block;
  transition: opacity 0.5s ease-in;
}

:deep(.markdown-image.visible) {
  opacity: 1;
}

:deep(.markdown-image.loaded) {
  opacity: 1;
}

:deep(.image-placeholder) {
  @apply absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800;
  z-index: -1;
}

:deep(.image-container.loaded .image-placeholder) {
  display: none;
}

:deep(.loading-spinner) {
  @apply w-8 h-8 border-4 border-gray-300 dark:border-gray-600 rounded-full border-t-primary-500;
  animation: spin 1s linear infinite;
}

:deep(.image-caption) {
  @apply text-sm text-center text-gray-500 dark:text-gray-400 mt-2;
  padding: 0.5rem;
  display: none;
}

:deep(.image-caption:not(:empty)) {
  display: block;
}

:deep(.image-error-message) {
  @apply absolute inset-0 flex items-center justify-center text-red-500 bg-gray-100 dark:bg-gray-800 font-medium;
  display: none;
}

:deep(.image-container.error .image-error-message) {
  display: flex;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 可点击图片的指示样式 */
:deep(.markdown-image.clickable) {
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

:deep(.markdown-image.clickable:hover) {
  transform: scale(1.02);
}

/* 图片查看器样式 */
.image-viewer {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(4px);
}

.image-viewer-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 90vw;
  max-height: 85vh;
}

.image-viewer-img {
  border-radius: 0.375rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  object-position: center;
  margin: auto;
  transition: transform 0.3s ease;
}

.image-viewer-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  transition: background 0.2s;
  z-index: 10000;
}

.image-viewer-close:hover {
  background: rgba(0, 0, 0, 0.8);
}

/* 缩放控制样式 */
.image-viewer-controls {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background-color: rgba(0, 0, 0, 0.7);
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  z-index: 60;
}

.control-btn {
  padding: 0.5rem;
  background-color: rgba(31, 41, 55, 0.8);
  color: white;
  border-radius: 9999px;
  transition: background-color 0.2s;
  outline: none;
  border: none;
  cursor: pointer;
}

.control-btn:hover {
  background-color: rgba(55, 65, 81, 0.9);
}

.zoom-level {
  font-size: 0.875rem;
  color: rgba(229, 231, 235, 1);
  margin: 0 0.5rem;
  font-weight: 500;
}

/* 移除图片名称显示 */
.markdown-body {
  img + em,
  img + br + em {
    display: none;
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