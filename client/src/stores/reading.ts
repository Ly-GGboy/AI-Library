import { defineStore } from 'pinia'

interface ReadingSettings {
  contentWidth: number
  fontSize: number
  autoHideControls: boolean
  enableAutoScroll: boolean
  theme: 'light' | 'dark' | 'sepia'
  lineHeight: number
  paragraphSpacing: number
  marginSize: number
}

interface ReadingState {
  isImmersive: boolean
  settings: ReadingSettings
  lastPosition: {
    path: string
    scroll: number
  } | null
  readingTime: {
    [key: string]: number  // 文档路径: 阅读时间（秒）
  }
}

export const useReadingStore = defineStore('reading', {
  state: (): ReadingState => ({
    isImmersive: false,
    settings: {
      contentWidth: 70,
      fontSize: 16,
      autoHideControls: true,
      enableAutoScroll: false,
      theme: 'light',
      lineHeight: 1.6,
      paragraphSpacing: 1.2,
      marginSize: 2
    },
    lastPosition: null,
    readingTime: {}
  }),

  actions: {
    setImmersiveMode(value: boolean) {
      this.isImmersive = value
      // 保存到本地存储
      localStorage.setItem('reading-immersive', String(value))
    },

    updateSettings(settings: Partial<ReadingSettings>) {
      this.settings = { ...this.settings, ...settings }
      // 保存到本地存储
      localStorage.setItem('reading-settings', JSON.stringify(this.settings))
    },

    savePosition(path: string, scroll: number) {
      this.lastPosition = { path, scroll }
      // 保存到本地存储
      localStorage.setItem('reading-position', JSON.stringify(this.lastPosition))
    },

    updateReadingTime(path: string, seconds: number) {
      if (!this.readingTime[path]) {
        this.readingTime[path] = 0
      }
      this.readingTime[path] += seconds
      // 保存到本地存储
      localStorage.setItem('reading-time', JSON.stringify(this.readingTime))
    },

    // 从本地存储恢复状态
    restoreState() {
      // 恢复沉浸式模式状态
      const immersive = localStorage.getItem('reading-immersive')
      if (immersive) {
        this.isImmersive = immersive === 'true'
      }

      // 恢复设置
      const settings = localStorage.getItem('reading-settings')
      if (settings) {
        this.settings = { ...this.settings, ...JSON.parse(settings) }
      }

      // 恢复上次阅读位置
      const position = localStorage.getItem('reading-position')
      if (position) {
        this.lastPosition = JSON.parse(position)
      }

      // 恢复阅读时间统计
      const readingTime = localStorage.getItem('reading-time')
      if (readingTime) {
        this.readingTime = JSON.parse(readingTime)
      }
    }
  },

  getters: {
    // 获取特定文档的阅读时间（格式化后的）
    getFormattedReadingTime: (state) => (path: string) => {
      const seconds = state.readingTime[path] || 0
      if (seconds < 60) {
        return `${seconds}秒`
      }
      const minutes = Math.floor(seconds / 60)
      if (minutes < 60) {
        return `${minutes}分钟`
      }
      const hours = Math.floor(minutes / 60)
      const remainingMinutes = minutes % 60
      return `${hours}小时${remainingMinutes}分钟`
    },

    // 获取所有文档的总阅读时间
    totalReadingTime: (state) => {
      return Object.values(state.readingTime).reduce((total, time) => total + time, 0)
    }
  }
}) 