import axios from 'axios'

// 将api变量导出以便其他模块直接使用
export const api = axios.create({
  baseURL: '/api',
  timeout: 100000,
  maxRedirects: 5,
  validateStatus: (status) => {
    return status >= 200 && status < 400
  }
})

// Add response interceptor for debugging
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Response Error:', error)
    return Promise.reject(error)
  }
)

export interface DocTree {
  name: string
  children: DocTree[]
  path?: string
  type?: string
  parent?: DocTree
}

export interface DocContent {
  path: string
  name: string
  content?: string
  last_modified: string
  size?: number
  type?: 'markdown' | 'pdf'
  page_count?: number
  estimated_reading_time?: number
}

export interface SearchResult {
  path: string
  name: string
  matches: Array<{
    type: string
    text: string
    line: number
  }>
  last_modified: string
}

export interface Breadcrumb {
  name: string
  path: string
}

export const docApi = {
  // 获取文档树
  getDocTree: async () => {
    const response = await api.get<DocTree>('/docs/tree')
    return response.data
  },

  // 获取文档内容
  getDocContent: async (path: string) => {
    const response = await api.get<DocContent>(`/docs/content/${path}`)
    return response.data
  },

  // 获取最近文档
  getRecentDocs: async (limit: number = 10) => {
    const response = await api.get<DocContent[]>('/docs/recent', {
      params: { limit }
    })
    return response.data
  },

  // 获取面包屑导航
  getBreadcrumb: async (path: string) => {
    const response = await api.get<Breadcrumb[]>(`/docs/breadcrumb/${path}`)
    return response.data
  }
}

export const searchApi = {
  // 搜索文档
  search: async (query: string, limit: number = 10) => {
    const response = await api.get<SearchResult[]>('/search', {
      params: { q: query, limit }
    })
    return response.data
  },

  // 获取搜索建议
  getSuggestions: async (query: string, limit: number = 5) => {
    const response = await api.get<string[]>('/search/suggest', {
      params: { q: query, limit }
    })
    return response.data
  }
}

// 管理后台API
export const adminAPI = {
  // 获取仪表盘数据
  getDashboard: () => api.get('/admin/dashboard'),
  
  // 获取详细统计数据
  getStats: () => api.get('/admin/stats'),
  
  // 获取热门文档
  getPopularDocs: (limit = 10) => api.get('/admin/popular-docs', { params: { limit } }),
  
  // 获取所有反馈
  getAllFeedback: (limit = 50) => api.get('/admin/feedback', { params: { limit } })
} 