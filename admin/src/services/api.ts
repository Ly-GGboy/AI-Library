import axios from 'axios'

// 创建API基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://localhost:8000'

// 创建Axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 10000,
  withCredentials: true // 添加这个配置以支持跨域请求携带cookie
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 可以在这里添加身份验证令牌等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('API请求错误:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// 管理后台API服务
export const adminAPI = {
  // 获取仪表盘统计数据
  getDashboardData: async () => {
    try {
      const response = await apiClient.get('/api/admin/dashboard')
      return response.data
    } catch (error) {
      console.error('获取仪表盘数据失败:', error)
      throw error
    }
  },

  // 获取访问统计数据
  getStats: async (timeRange = '7d') => {
    try {
      const response = await apiClient.get('/api/admin/stats', {
        params: { range: timeRange }
      })
      return response.data
    } catch (error) {
      console.error('获取访问统计数据失败:', error)
      throw error
    }
  },

  // 获取热门文档
  getPopularDocuments: async (limit = 10) => {
    try {
      const response = await apiClient.get('/api/admin/popular-docs', {
        params: { limit }
      })
      return response.data
    } catch (error) {
      console.error('获取热门文档失败:', error)
      throw error
    }
  },

  // 获取用户反馈
  getFeedback: async (params = {}) => {
    try {
      const response = await apiClient.get('/api/admin/feedback', { params })
      return response.data
    } catch (error) {
      console.error('获取用户反馈失败:', error)
      throw error
    }
  },

  // 回复用户反馈
  replyToFeedback: async (feedbackId: string, replyText: string) => {
    try {
      const response = await apiClient.post(`/api/admin/feedback/${feedbackId}/reply`, {
        reply_text: replyText
      })
      return response.data
    } catch (error) {
      console.error('回复反馈失败:', error)
      throw error
    }
  }
}

export default apiClient 