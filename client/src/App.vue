<template>
  <div :class="currentTheme">
    <RouterView />
    <div class="global-controls" v-if="shouldShowReadingControls">
      <ReadingControls />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { useReadingStore } from './stores/reading'
import { useThemeStore } from './stores/theme'
import { computed, onMounted, watch } from 'vue'
import ReadingControls from './components/ReadingControls.vue'

const readingStore = useReadingStore()
const themeStore = useThemeStore()
const route = useRoute()

// 计算当前主题
const currentTheme = computed(() => {
  return themeStore.isDark ? 'dark' : 'light'
})

// 仅在文档页面显示阅读控制器
const shouldShowReadingControls = computed(() => {
  return route.name === 'doc' // 假设文档页面的路由名为'doc'
})

// 监听主题变化
watch(() => currentTheme.value, (newTheme) => {
  document.documentElement.classList.remove('light', 'dark', 'sepia')
  document.documentElement.classList.add(newTheme)
})

// 组件挂载时恢复保存的主题
onMounted(() => {
  readingStore.restoreState()
  
  // 统一使用theme store的主题设置
  const isDark = themeStore.isDark
  document.documentElement.classList.add(isDark ? 'dark' : 'light')
})
</script>

<style>
@import './styles/immersive.css';

.global-controls {
  position: fixed;
  top: 5rem;
  right: 1rem;
  z-index: 50; /* 降低z-index，避免遮挡公告板 */
}

/* 全局主题样式 */
.light {
  --bg-color: #ffffff;
  --text-color: #1f2937;
  --primary-color: 59, 130, 246;
}

.dark {
  --bg-color: #1f2937;
  --text-color: #f3f4f6;
  --primary-color: 96, 165, 250;
}

.sepia {
  --bg-color: #f5f1e6;
  --text-color: #444444;
  --primary-color: 107, 95, 78;
}

/* 应用全局背景色 */
#app {
  min-height: 100vh;
  background: var(--bg-color);
  color: var(--text-color);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* 确保公告板按钮始终可见 */
.announcement-button {
  visibility: visible !important;
  display: block !important;
  opacity: 1 !important;
  z-index: 95 !important; /* 高于阅读控制器但低于弹出层 */
}
</style>
