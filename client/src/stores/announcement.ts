import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../services/api'

interface UpdateItem {
  id: string;
  title: string;
  description: string;
  date: string;
  changes?: string[];
  important?: boolean;
}

interface RecommendationItem {
  id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
  path?: string;
  url?: string;
}

interface FeedbackItem {
  name: string;
  type: string;
  content: string;
  contact: string;
  timestamp: string;
}

export const useAnnouncementStore = defineStore('announcement', () => {
  // 状态
  const updates = ref<UpdateItem[]>([])
  const recommendations = ref<RecommendationItem[]>([])
  const lastViewedUpdateTime = ref<string>(localStorage.getItem('lastViewedUpdateTime') || '')
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // 计算属性
  const hasNewUpdates = computed(() => {
    if (!updates.value.length || !lastViewedUpdateTime.value) return false
    
    const lastViewTime = new Date(lastViewedUpdateTime.value).getTime()
    const latestUpdateTime = new Date(updates.value[0].date).getTime()
    
    return latestUpdateTime > lastViewTime
  })

  // 方法
  const getUpdates = async () => {
    loading.value = true
    error.value = null
    
    try {
      // 尝试从API获取数据
      const response = await api.get('/announcements/updates')
      updates.value = response.data
      return updates.value
    } catch (err) {
      console.error('Failed to fetch updates:', err)
      error.value = '获取更新信息失败'
      
      // 如果API请求失败，使用模拟数据
      const mockUpdates = [
        {
          id: '1',
          title: 'AI Library 1.0 发布',
          description: '我们很高兴地宣布 AI Library 1.0 正式发布！通过本系统，您可以轻松浏览和学习AI相关知识。',
          date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          changes: ['支持Markdown文档阅读', '树形目录结构浏览', '支持深色模式'],
          important: true
        },
        {
          id: '2',
          title: '新增公告板功能',
          description: '现在您可以通过公告板了解最新的更新和推荐内容，并向我们提供反馈。',
          date: new Date().toISOString(),
          changes: ['项目更新通知', '内容推荐功能', '用户反馈收集'],
          important: true
        }
      ]
      
      return mockUpdates
    } finally {
      loading.value = false
    }
  }

  const getRecommendations = async () => {
    loading.value = true
    error.value = null
    
    try {
      // 尝试从API获取数据
      const response = await api.get('/announcements/recommendations')
      recommendations.value = response.data
      return recommendations.value
    } catch (err) {
      console.error('Failed to fetch recommendations:', err)
      error.value = '获取推荐内容失败'
      
      // 如果API请求失败，使用模拟数据
      const mockRecommendations = [
        {
          id: '1',
          title: 'AI基础知识入门',
          description: '了解人工智能的基本概念和应用场景，适合完全没有AI基础的初学者。',
          category: '入门系列',
          tags: ['AI入门', '基础知识'],
          path: '/ai-basics'
        },
        {
          id: '2',
          title: 'Python编程基础',
          description: '学习Python编程的基础知识，为深入学习AI打下基础。',
          category: '编程基础',
          tags: ['Python', '编程基础'],
          path: '/python-basics'
        },
        {
          id: '3',
          title: 'ChatGPT使用指南',
          description: '如何有效利用ChatGPT提升工作和学习效率，避免常见的使用误区。',
          category: '实用指南',
          tags: ['ChatGPT', '提示工程'],
          url: 'https://openai.com/blog/chatgpt'
        }
      ]
      
      return mockRecommendations
    } finally {
      loading.value = false
    }
  }

  const submitFeedback = async (feedback: FeedbackItem) => {
    loading.value = true
    error.value = null
    
    try {
      await api.post('/feedback', feedback)
    } catch (err) {
      console.error('Failed to submit feedback:', err)
      error.value = '提交反馈失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  const markUpdatesAsViewed = () => {
    // 记录最新查看的时间
    const now = new Date().toISOString()
    lastViewedUpdateTime.value = now
    localStorage.setItem('lastViewedUpdateTime', now)
  }

  return {
    updates,
    recommendations,
    loading,
    error,
    hasNewUpdates,
    getUpdates,
    getRecommendations,
    submitFeedback,
    markUpdatesAsViewed
  }
}) 