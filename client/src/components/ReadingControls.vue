<template>
  <div class="reading-controls" :class="{ 'immersive': isImmersive }">
    <!-- 主控制栏 -->
    <div class="controls-bar" :class="{ 'hidden': isImmersive && !showControls }">
      <!-- 沉浸式阅读按钮 -->
      <button 
        v-if="!isImmersive"
        class="control-btn immersive-btn"
        @click="toggleImmersive"
        :title="`${isMac ? '⌘' : 'Ctrl'} + Shift + R`"
      >
        <ArrowsPointingOutIcon class="w-5 h-5" />
        <span class="btn-text">沉浸阅读</span>
      </button>

      <!-- 退出沉浸按钮 -->
      <button 
        v-if="isImmersive"
        class="control-btn exit-btn"
        @click="toggleImmersive"
        :title="`${isMac ? '⌘' : 'Ctrl'} + Shift + R`"
      >
        <ArrowsPointingInIcon class="w-5 h-5" />
        <span class="btn-text">退出沉浸</span>
      </button>

      <!-- 分隔线 -->
      <div class="divider"></div>

      <!-- 阅读设置 -->
      <button 
        class="control-btn"
        @click="toggleSettings"
        :title="'阅读设置'"
      >
        <Cog6ToothIcon class="w-5 h-5" />
      </button>

      <!-- 阅读进度 -->
      <div class="reading-progress" v-if="isImmersive">
        <div class="progress-bar" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ progress }}%</span>
      </div>
    </div>

    <!-- 设置面板 -->
    <Transition name="slide">
      <div v-if="showSettings" class="settings-panel">
        <div class="panel-header">
          <h3>阅读设置</h3>
          <button @click="toggleSettings" class="close-btn">
            <XMarkIcon class="w-5 h-5" />
          </button>
        </div>
        
        <!-- 布局设置 -->
        <div class="setting-section">
          <h4>布局</h4>
          <div class="setting-item">
            <label>内容宽度</label>
            <input 
              type="range" 
              v-model="settings.contentWidth" 
              min="60" 
              max="95" 
              step="5"
              @input="updateStyles"
            />
            <span>{{ settings.contentWidth }}%</span>
          </div>
          
          <div class="setting-item">
            <label>字体大小</label>
            <input 
              type="range" 
              v-model="settings.fontSize" 
              min="14" 
              max="24" 
              step="1"
              @input="updateStyles"
            />
            <span>{{ settings.fontSize }}px</span>
          </div>

          <div class="setting-item">
            <label>行高</label>
            <input 
              type="range" 
              v-model="settings.lineHeight" 
              min="1.4" 
              max="2.0" 
              step="0.1"
              @input="updateStyles"
            />
            <span>{{ settings.lineHeight }}</span>
          </div>

          <div class="setting-item">
            <label>段落间距</label>
            <input 
              type="range" 
              v-model="settings.paragraphSpacing" 
              min="1.0" 
              max="2.0" 
              step="0.1"
              @input="updateStyles"
            />
            <span>{{ settings.paragraphSpacing }}rem</span>
          </div>
        </div>

        <!-- 显示设置 -->
        <div class="setting-section">
          <h4>显示</h4>
          <div class="setting-item">
            <label>
              <input 
                type="checkbox" 
                v-model="settings.autoHideControls"
              />
              自动隐藏控制栏
            </label>
          </div>
          
          <div class="setting-item">
            <label>
              <input 
                type="checkbox" 
                v-model="settings.enableAutoScroll"
              />
              启用自动滚动
            </label>
          </div>

          <div class="setting-item" v-if="settings.enableAutoScroll">
            <label>滚动速度</label>
            <input 
              type="range" 
              v-model="settings.scrollSpeed" 
              min="1" 
              max="10" 
              step="1"
            />
            <span>{{ settings.scrollSpeed }}</span>
          </div>
        </div>

        <!-- 主题设置 -->
        <div class="setting-section">
          <h4>主题</h4>
          <div class="theme-buttons">
            <button 
              class="theme-btn"
              :class="{ active: settings.theme === 'light' }"
              @click="setTheme('light')"
            >
              <SunIcon class="w-5 h-5" />
              <span>浅色</span>
            </button>
            <button 
              class="theme-btn"
              :class="{ active: settings.theme === 'dark' }"
              @click="setTheme('dark')"
            >
              <MoonIcon class="w-5 h-5" />
              <span>深色</span>
            </button>
            <button 
              class="theme-btn"
              :class="{ active: settings.theme === 'sepia' }"
              @click="setTheme('sepia')"
            >
              <BookOpenIcon class="w-5 h-5" />
              <span>护眼</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useReadingStore } from '../stores/reading'
import { useThemeStore } from '../stores/theme'
import { 
  ArrowsPointingInIcon, 
  ArrowsPointingOutIcon,
  Cog6ToothIcon,
  XMarkIcon,
  SunIcon,
  MoonIcon,
  BookOpenIcon
} from '@heroicons/vue/24/outline'

const readingStore = useReadingStore()
const themeStore = useThemeStore()
const isImmersive = ref(false)
const showControls = ref(true)
const showSettings = ref(false)
const progress = ref(0)

// 检测是否为 Mac 系统
const isMac = computed(() => {
  return navigator.platform.toUpperCase().indexOf('MAC') >= 0
})

// 阅读设置
const settings = ref({
  contentWidth: 90,
  fontSize: 16,
  lineHeight: 1.6,
  paragraphSpacing: 1.2,
  autoHideControls: true,
  enableAutoScroll: false,
  scrollSpeed: 5,
  theme: 'light'
})

// 更新样式变量
const updateStyles = () => {
  const root = document.documentElement
  root.style.setProperty('--reading-content-width', `${settings.value.contentWidth}%`)
  root.style.setProperty('--reading-font-size', `${settings.value.fontSize}px`)
  root.style.setProperty('--reading-line-height', settings.value.lineHeight.toString())
  root.style.setProperty('--reading-paragraph-spacing', `${settings.value.paragraphSpacing}rem`)
}

// 设置主题
const setTheme = (theme: 'light' | 'dark' | 'sepia') => {
  settings.value.theme = theme
  
  // 更新全局主题状态
  if (theme === 'dark') {
    themeStore.setTheme(true)
  } else if (theme === 'light') {
    themeStore.setTheme(false)
  }
  
  document.documentElement.classList.remove('light', 'dark', 'sepia')
  document.documentElement.classList.add(theme)
  readingStore.updateSettings({ theme })
}

// 切换沉浸式模式
const toggleImmersive = () => {
  isImmersive.value = !isImmersive.value
  readingStore.setImmersiveMode(isImmersive.value)
  
  if (isImmersive.value) {
    document.documentElement.classList.add('immersive-reading')
    updateStyles()
  } else {
    document.documentElement.classList.remove('immersive-reading')
  }
}

// 切换设置面板
const toggleSettings = () => {
  showSettings.value = !showSettings.value
}

// 自动隐藏控制栏
let hideTimeout: number | null = null
const startHideTimer = () => {
  if (!settings.value.autoHideControls) return
  if (hideTimeout) clearTimeout(hideTimeout)
  hideTimeout = window.setTimeout(() => {
    if (!showSettings.value) {
      showControls.value = false
    }
  }, 2000)
}

const clearHideTimer = () => {
  if (hideTimeout) {
    clearTimeout(hideTimeout)
    hideTimeout = null
  }
  showControls.value = true
}

// 自动滚动
let scrollInterval: number | null = null
const startAutoScroll = () => {
  if (!settings.value.enableAutoScroll) return
  stopAutoScroll()
  scrollInterval = window.setInterval(() => {
    window.scrollBy({
      top: settings.value.scrollSpeed,
      behavior: 'smooth'
    })
  }, 50)
}

const stopAutoScroll = () => {
  if (scrollInterval) {
    clearInterval(scrollInterval)
    scrollInterval = null
  }
}

// 监听鼠标移动
const handleMouseMove = () => {
  clearHideTimer()
  startHideTimer()
}

// 监听快捷键
const handleKeydown = (e: KeyboardEvent) => {
  // Ctrl/Cmd + Shift + R
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'r') {
    e.preventDefault()
    toggleImmersive()
  }
}

// 更新阅读进度
const updateProgress = () => {
  const element = document.documentElement
  const totalHeight = element.scrollHeight - element.clientHeight
  const currentPosition = element.scrollTop
  progress.value = Math.round((currentPosition / totalHeight) * 100)
}

// 监听设置变化
watch(() => settings.value.enableAutoScroll, (newValue) => {
  if (newValue) {
    startAutoScroll()
  } else {
    stopAutoScroll()
  }
})

// 组件挂载
onMounted(() => {
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('scroll', updateProgress)
  startHideTimer()

  // 恢复保存的设置
  const savedSettings = readingStore.settings
  if (savedSettings) {
    settings.value = { ...settings.value, ...savedSettings }
    
    // 从ThemeStore获取当前主题
    const currentTheme = themeStore.isDark ? 'dark' : 'light'
    settings.value.theme = currentTheme
    
    updateStyles()
  }
})

// 组件卸载
onUnmounted(() => {
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('scroll', updateProgress)
  if (hideTimeout) clearTimeout(hideTimeout)
  stopAutoScroll()
})
</script>

<style scoped>
.reading-controls {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 9999;
  transition: all 0.3s ease;
}

.controls-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: white;
  backdrop-filter: blur(8px);
  padding: 0.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dark .controls-bar {
  background: #1f2937;
}

.sepia .controls-bar {
  background: var(--sepia-bg);
}

.controls-bar.hidden {
  opacity: 0;
  transform: translateY(-1rem);
  pointer-events: none;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  background: transparent;
  color: var(--text-color);
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: rgba(var(--primary-color), 0.1);
}

.control-btn.active {
  background: rgba(var(--primary-color), 0.15);
  color: rgb(var(--primary-color));
}

.btn-text {
  font-size: 0.9rem;
  font-weight: 500;
}

.divider {
  width: 1px;
  height: 1.5rem;
  background: rgba(var(--text-color), 0.2);
}

.reading-progress {
  position: relative;
  width: 100px;
  height: 4px;
  background: rgba(var(--text-color), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: rgb(var(--primary-color));
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  right: -2rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.8rem;
  color: rgba(var(--text-color), 0.6);
}

.settings-panel {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  padding: 1rem;
  z-index: 9999;
}

.dark .settings-panel {
  background: #1f2937;
}

.sepia .settings-panel {
  background: var(--sepia-bg);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color);
}

.dark .panel-header h3 {
  color: rgba(255, 255, 255, 0.9);
}

.close-btn {
  padding: 0.25rem;
  border-radius: 4px;
  color: rgba(var(--text-color), 0.6);
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(var(--text-color), 0.1);
  color: rgba(var(--text-color), 0.8);
}

.setting-section {
  margin-bottom: 1.5rem;
}

.setting-section h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.75rem;
}

.dark .setting-section h4 {
  color: rgba(255, 255, 255, 0.9);
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.setting-item label {
  flex: 1;
  font-size: 0.9rem;
  color: var(--text-color);
}

.dark .setting-item label {
  color: rgba(255, 255, 255, 0.8);
}

.setting-item input[type="range"] {
  width: 120px;
}

.setting-item input[type="checkbox"] {
  margin-right: 0.5rem;
}

.setting-item span {
  font-size: 0.8rem;
  color: var(--text-color);
  width: 3rem;
  text-align: right;
}

.dark .setting-item span {
  color: rgba(255, 255, 255, 0.7);
}

.theme-buttons {
  display: flex;
  gap: 0.5rem;
}

.theme-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border-radius: 8px;
  background: rgba(var(--text-color), 0.05);
  color: var(--text-color);
  transition: all 0.2s ease;
}

.theme-btn:hover {
  background: rgba(var(--text-color), 0.1);
}

.theme-btn.active {
  background: rgba(var(--primary-color), 0.15);
  color: rgb(var(--primary-color));
}

.dark .theme-btn {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
}

.dark .theme-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dark .theme-btn.active {
  background: rgba(var(--primary-color), 0.2);
  color: rgb(var(--primary-color));
}

.sepia .theme-btn {
  background: rgba(107, 95, 78, 0.05);
  color: var(--sepia-text);
}

.sepia .theme-btn:hover {
  background: rgba(107, 95, 78, 0.1);
}

.sepia .theme-btn.active {
  background: rgba(107, 95, 78, 0.15);
  color: var(--sepia-link);
}

.theme-btn span {
  font-size: 0.8rem;
  font-weight: 500;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-0.5rem);
}
</style> 