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

// 更新阅读进度
const updateProgress = () => {
  const element = document.documentElement
  const totalHeight = element.scrollHeight - element.clientHeight
  const currentPosition = element.scrollTop
  progress.value = Math.round((currentPosition / totalHeight) * 100)
}

// 监听阅读模式变化
watch(() => readingStore.isImmersive, (newValue) => {
  isImmersive.value = newValue
  if (newValue) {
    document.documentElement.classList.add('immersive-reading')
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
  
  // 添加滚动监听
  window.addEventListener('scroll', updateProgress)
})

// 组件卸载
onUnmounted(() => {
  window.removeEventListener('scroll', updateProgress)
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
  transition: width 0.3s ease;
  z-index: 1000;
}
</style> 