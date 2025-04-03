<template>
  <div class="immersive-reader" :class="{ 'active': isImmersive }">
    <!-- 原有的文档查看器 -->
    <slot></slot>
    
    <!-- 阅读进度指示器 -->
    <div 
      v-if="isImmersive" 
      class="reading-progress-bar"
      :style="{ width: `${progress}%` }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useReadingStore } from '../stores/reading'
import { useRoute } from 'vue-router'

const readingStore = useReadingStore()
const route = useRoute()

// 组件状态
const isImmersive = ref(false)
const progress = ref(0)

// 监听路由变化
watch(() => route.path, (newPath, oldPath) => {
  // 如果是新路径，滚动到顶部
  if (newPath !== oldPath) {
    window.scrollTo(0, 0)
  }
  // 保存上次阅读位置
  if (oldPath && isImmersive.value) {
    saveReadingPosition()
  }
})

// 保存阅读位置
const saveReadingPosition = () => {
  const scrollPosition = window.scrollY
  readingStore.savePosition(route.path, scrollPosition)
}

// 更新阅读进度 - 添加防抖
let progressUpdateTimer: number | null = null;

const updateProgress = () => {
  // 防抖处理
  if (progressUpdateTimer) {
    window.clearTimeout(progressUpdateTimer);
  }
  
  progressUpdateTimer = window.setTimeout(() => {
    // 使用简化的进度计算
    const mainContent = document.querySelector('main')
    if (!mainContent) return
    
    // 调试分析DOM结构
    console.log('ImmersiveReader DOM Structure:', {
      main: !!mainContent,
      immersiveClass: document.documentElement.classList.contains('immersive-reading'),
      scrollTop: mainContent.scrollTop,
      scrollHeight: mainContent.scrollHeight,
      clientHeight: mainContent.clientHeight
    });
    
    // 使用主容器的滚动位置计算
    const scrollHeight = mainContent.scrollHeight
    const clientHeight = mainContent.clientHeight
    const scrollTop = mainContent.scrollTop
    
    // 总可滚动距离
    const scrollableDistance = scrollHeight - clientHeight
    
    // 确保没有负值导致的异常计算
    if (scrollableDistance <= 0) {
      progress.value = 0
      return
    }
    
    // 确保滚动位置不超出边界
    const boundedScrollTop = Math.max(0, Math.min(scrollTop, scrollableDistance))
    
    // 计算滚动百分比并确保在 0-100 范围内
    const percentage = (boundedScrollTop / scrollableDistance) * 100
    const newProgress = Math.max(0, Math.min(100, Math.round(percentage)))
    
    // 仅在进度值变化时更新
    if (progress.value !== newProgress) {
      progress.value = newProgress
    }
  }, 50); // 50ms防抖
}

// 监听阅读模式变化
watch(() => readingStore.isImmersive, (newValue) => {
  isImmersive.value = newValue
  if (newValue) {
    document.documentElement.classList.add('immersive-reading')
    // 当切换到沉浸模式时重新计算进度
    setTimeout(updateProgress, 100); 
  } else {
    document.documentElement.classList.remove('immersive-reading')
  }
})

// 组件挂载
onMounted(() => {
  // 恢复状态
  readingStore.restoreState()
  isImmersive.value = readingStore.isImmersive
  
  // 新页面总是从顶部开始
  window.scrollTo(0, 0)
  
  // 详细滚动事件监听
  // 1. 监听window滚动事件
  window.removeEventListener('scroll', updateProgress)
  window.addEventListener('scroll', updateProgress, { passive: true })
  console.log('ImmersiveReader: Added scroll listener to window')
  
  // 2. 监听主内容区域滚动事件
  const mainContent = document.querySelector('main')
  if (mainContent) {
    mainContent.removeEventListener('scroll', updateProgress)
    mainContent.addEventListener('scroll', updateProgress, { passive: true })
    console.log('ImmersiveReader: Added scroll listener to main content')
  } else {
    console.warn('ImmersiveReader: Main content element not found')
  }
  
  // 3. 监听markdown-body内容区域（如果存在）
  const markdownBody = document.querySelector('.markdown-body')
  if (markdownBody) {
    markdownBody.removeEventListener('scroll', updateProgress)
    markdownBody.addEventListener('scroll', updateProgress, { passive: true })
    console.log('ImmersiveReader: Added scroll listener to markdown-body')
  }
  
  // 监听文档滚动事件，包括所有可能的容器元素
  document.addEventListener('scroll', (e) => {
    console.log('Document scroll event detected on:', e.target)
    updateProgress()
  }, { passive: true, capture: true })
  
  // 初始进度计算，延迟执行以确保DOM已完全加载
  setTimeout(updateProgress, 100)
})

// 组件卸载
onUnmounted(() => {
  // 移除所有滚动监听
  window.removeEventListener('scroll', updateProgress)
  
  const mainContent = document.querySelector('main')
  if (mainContent) {
    mainContent.removeEventListener('scroll', updateProgress)
  }
  
  const markdownBody = document.querySelector('.markdown-body')
  if (markdownBody) {
    markdownBody.removeEventListener('scroll', updateProgress)
  }
  
  document.removeEventListener('scroll', updateProgress, { capture: true })
  
  // 清理防抖定时器
  if (progressUpdateTimer) {
    clearTimeout(progressUpdateTimer)
  }
  
  if (isImmersive.value) {
    saveReadingPosition()
  }
})
</script>

<style>
@import '../styles/immersive.css';
</style>

<style scoped>
.immersive-reader {
  position: relative;
  min-height: 100vh;
  transition: all 0.3s ease;
}

.immersive-reader.active {
  background: var(--bg-color);
}

.reading-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 2px;
  background: var(--primary-color);
  transition: width 0.1s linear;
  z-index: 1000;
}
</style> 