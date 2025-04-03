<style scoped>
.doc-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
  /* 确保容器占满可用空间 */
  min-height: 100vh;
  padding-top: var(--header-height, 3rem);
  box-sizing: border-box;
}

main {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  position: relative;
  width: 100%;
  background: var(--bg-color);
  
  /* 移除可能导致内容被截断的高度限制 */
  height: auto;
  min-height: calc(100vh - var(--header-height, 3rem) - var(--footer-height, 3rem));
}

/* 移动端适配 */
@media (max-width: 768px) {
  .doc-view {
    position: relative;
    height: auto;
    min-height: 100vh;
    padding-top: var(--header-height, 3rem);
    padding-bottom: var(--footer-height, 3rem);
  }

  main {
    position: relative;
    height: auto;
    min-height: calc(100vh - var(--header-height, 3rem) - var(--footer-height, 3rem));
    padding: 1rem;
    margin-bottom: 3rem; /* 为底部工具栏留出空间 */
  }

  /* 非沉浸模式下的样式调整 */
  .doc-view.no-immersive {
    main {
      height: auto;
      min-height: calc(100vh - var(--header-height, 3rem) - var(--footer-height, 3rem));
    }
  }
}

/* 确保内容区域始终可见 */
:deep(.markdown-body) {
  min-height: 100%;
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
  box-sizing: border-box;
  background: var(--bg-color);
  
  /* 确保内容可见 */
  color: var(--text-color);
  
  /* 添加一些基础样式 */
  font-size: 16px;
  line-height: 1.6;
}

/* 工具栏固定在底部 */
:deep(.reading-controls) {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
  height: var(--footer-height, 3rem);
  padding: 0.5rem 1rem;
  box-sizing: border-box;
}
</style>

<template>
  <div class="doc-view" :class="{ 'no-immersive': !isImmersive }">
    <main ref="mainContent" @scroll="handleScroll">
      <article class="markdown-body" v-if="docStore.currentDoc">
        <div v-if="docStore.currentDoc.content" class="markdown-content">
          <MarkdownViewer :content="docStore.currentDoc.content" />
        </div>
        <div v-else-if="isPDF" class="pdf-content">
          <PDFViewer :path="docStore.currentDoc.path || ''" />
        </div>
        <div v-else class="empty-state">
          无法显示文档内容
        </div>
      </article>
      <div v-else class="empty-state">
        请选择一个文档
      </div>
    </main>
    <ReadingControls 
      :progress="readingProgress"
      :is-immersive="isImmersive"
      @toggle-immersive="toggleImmersive"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted, computed, watch } from 'vue'
import { useDocStore } from '../stores/doc'
import MarkdownViewer from './MarkdownViewer.vue'
import PDFViewer from './PDFViewer.vue'
import ReadingControls from './ReadingControls.vue'

const docStore = useDocStore()

// 计算是否为PDF文档
const isPDF = computed(() => docStore.currentDoc?.type === 'pdf')

// 阅读进度
const readingProgress = ref(0)

// 添加响应式布局相关的逻辑
const isImmersive = ref(false)
const mainContent = ref<HTMLElement | null>(null)

// 监听文档变化，重置滚动位置
watch(() => docStore.currentDoc, () => {
  if (mainContent.value) {
    mainContent.value.scrollTop = 0
    readingProgress.value = 0
  }
}, { immediate: true })

const toggleImmersive = () => {
  isImmersive.value = !isImmersive.value
  // 切换模式后触发重新布局
  nextTick(() => {
    if (mainContent.value) {
      mainContent.value.style.height = isImmersive.value ? '100vh' : 'auto'
      // 触发一次滚动事件以更新进度
      updateProgress(mainContent.value)
    }
  })
}

// 更新进度的辅助函数
const updateProgress = (element: HTMLElement) => {
  const scrollTop = element.scrollTop
  const scrollHeight = element.scrollHeight
  const clientHeight = element.clientHeight
  const scrollableDistance = scrollHeight - clientHeight
  
  if (scrollableDistance <= 0) {
    readingProgress.value = 0
    return
  }
  
  const progress = (scrollTop / scrollableDistance) * 100
  readingProgress.value = Math.min(100, Math.max(0, progress))
}

const handleScroll = (event: Event) => {
  const target = event.target as HTMLElement
  if (!target) return
  updateProgress(target)
}

// 监听窗口大小变化
onMounted(() => {
  const handleResize = () => {
    if (mainContent.value) {
      // 根据当前模式设置合适的高度
      mainContent.value.style.height = isImmersive.value ? '100vh' : 'auto'
      // 触发一次滚动事件以更新进度
      updateProgress(mainContent.value)
    }
  }
  
  window.addEventListener('resize', handleResize)
  handleResize() // 初始化时调用一次
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
  })
})
</script> 