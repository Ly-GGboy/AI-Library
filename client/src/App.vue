<template>
  <div :class="currentTheme">
    <RouterView />
    <div class="global-controls">
      <ReadingControls />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useReadingStore } from './stores/reading'
import { computed, onMounted, watch } from 'vue'
import ReadingControls from './components/ReadingControls.vue'

const readingStore = useReadingStore()

// 计算当前主题
const currentTheme = computed(() => {
  return readingStore.settings.theme || 'light'
})

// 监听主题变化
watch(() => currentTheme.value, (newTheme) => {
  document.documentElement.classList.remove('light', 'dark', 'sepia')
  document.documentElement.classList.add(newTheme)
})

// 组件挂载时恢复保存的主题
onMounted(() => {
  readingStore.restoreState()
  if (readingStore.settings.theme) {
    document.documentElement.classList.add(readingStore.settings.theme)
  }
})
</script>

<style>
@import './styles/immersive.css';

.global-controls {
  position: fixed;
  top: 5rem;
  right: 1rem;
  z-index: 99;
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
</style>
