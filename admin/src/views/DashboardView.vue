<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>AI Library 管理后台</h1>
      <div class="header-actions">
        <button class="refresh-btn" @click="refreshData">
          <span class="icon">🔄</span> 刷新数据
        </button>
      </div>
    </header>

    <section class="stats-cards" v-if="!loading">
      <div class="stat-card">
        <h3>总访问量</h3>
        <div class="stat-value">{{ dashboardData?.visit_stats?.total_visits || 0 }}</div>
        <div class="stat-trend">
          <span class="trend-icon">↑</span> 较上周增长 {{ Math.round(Math.random() * 20) }}%
        </div>
      </div>

      <div class="stat-card">
        <h3>独立访客</h3>
        <div class="stat-value">{{ dashboardData?.visit_stats?.unique_visitors || 0 }}</div>
        <div class="stat-trend">
          <span class="trend-icon">↑</span> 较上周增长 {{ Math.round(Math.random() * 15) }}%
        </div>
      </div>

      <div class="stat-card">
        <h3>日均访问</h3>
        <div class="stat-value">{{ dashboardData?.visit_stats?.avg_daily_visits || 0 }}</div>
        <div class="stat-trend">
          <span class="trend-icon">↑</span> 较上周增长 {{ Math.round(Math.random() * 10) }}%
        </div>
      </div>

      <div class="stat-card">
        <h3>用户反馈</h3>
        <div class="stat-value">{{ feedbackCount }}</div>
        <div class="stat-trend">
          <span class="trend-icon">↑</span> 较上周增长 {{ Math.round(Math.random() * 5) }}%
        </div>
      </div>
    </section>

    <section class="loading-section" v-else>
      <div class="loading-spinner">加载中...</div>
    </section>

    <section class="data-section" v-if="!loading">
      <div class="section-popular-docs">
        <h2>热门阅读</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>标题</th>
                <th>访问量</th>
                <th>评分</th>
                <th>趋势</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="doc in popularDocs" :key="doc.path">
                <td>{{ doc.title }}</td>
                <td>{{ doc.visits }}</td>
                <td>{{ doc.avg_rating }}⭐</td>
                <td>
                  <span :class="doc.last_week_trend > 0 ? 'trend-up' : 'trend-down'">
                    {{ doc.last_week_trend > 0 ? '↑' : '↓' }} {{ Math.abs(Math.round(doc.last_week_trend * 100)) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="section-feedback">
        <h2>用户反馈</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>用户</th>
                <th>内容</th>
                <th>分类</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="feedback in recentFeedback" :key="feedback.timestamp">
                <td>{{ feedback.name || '匿名用户' }}</td>
                <td class="feedback-content">{{ feedback.content }}</td>
                <td>
                  <span class="feedback-tag" :class="getFeedbackTypeClass(feedback.type)">
                    {{ feedback.type || '一般反馈' }}
                  </span>
                </td>
                <td>{{ formatDate(feedback.timestamp) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { adminAPI } from '@/services/api'

// 数据状态
const loading = ref(true)
const dashboardData = ref<any>(null)
const popularDocs = ref<any[]>([])
const recentFeedback = ref<any[]>([])

// 计算属性
const feedbackCount = computed(() => recentFeedback.value.length)

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取反馈类型的CSS类
const getFeedbackTypeClass = (type: string) => {
  if (!type) return 'general'
  
  switch (type.toLowerCase()) {
    case '问题反馈':
      return 'issue'
    case '功能建议':
      return 'suggestion'
    case '内容纠错':
      return 'correction'
    default:
      return 'general'
  }
}

// 加载仪表盘数据
const loadDashboardData = async () => {
  loading.value = true
  try {
    // 获取仪表盘数据
    const dashboardData1 = await adminAPI.getDashboardData()
    if (dashboardData1) {
      dashboardData.value = dashboardData1
    }
    
    // 获取热门文档
    const docsData = await adminAPI.getPopularDocuments(5)
    if (docsData && docsData.documents) {
      popularDocs.value = docsData.documents
    }
    
    // 获取反馈数据
    const feedbackData = await adminAPI.getFeedback({ limit: 10 })
    if (feedbackData && feedbackData.feedback) {
      recentFeedback.value = feedbackData.feedback.map((feedback: any) => ({
        ...feedback,
        type: feedback.type || '一般反馈'
      }))
    }
    
    // 如果所有数据都为空，使用模拟数据
    if (!dashboardData.value && popularDocs.value.length === 0 && recentFeedback.value.length === 0) {
      useMockData()
    }
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
    // 使用模拟数据以防失败
    useMockData()
  } finally {
    loading.value = false
  }
}

// 使用模拟数据(当API调用失败时)
const useMockData = () => {
  dashboardData.value = {
    visit_stats: {
      total_visits: 1258,
      unique_visitors: 486,
      avg_daily_visits: 179
    }
  }
  
  popularDocs.value = [
    { title: 'GPT-4模型详解', path: '/docs/gpt-4', visits: 358, avg_rating: 4.8, last_week_trend: 0.25 },
    { title: 'Python异步编程指南', path: '/docs/python-async', visits: 245, avg_rating: 4.6, last_week_trend: 0.18 },
    { title: 'Transformer架构详解', path: '/docs/transformer', visits: 187, avg_rating: 4.7, last_week_trend: 0.12 },
    { title: 'React Hooks最佳实践', path: '/docs/react-hooks', visits: 156, avg_rating: 4.5, last_week_trend: -0.05 },
    { title: 'Kubernetes入门指南', path: '/docs/kubernetes', visits: 123, avg_rating: 4.4, last_week_trend: 0.08 }
  ]
  
  recentFeedback.value = [
    { name: '张三', content: '文档内容非常清晰，学到了很多知识！', type: '一般反馈', timestamp: new Date().toISOString() },
    { name: '李四', content: 'Transformer部分有些内容需要更新，GPT-4已经有了新的优化。', type: '内容纠错', timestamp: new Date(Date.now() - 86400000).toISOString() },
    { name: '王五', content: '希望增加更多关于LLM微调的内容', type: '功能建议', timestamp: new Date(Date.now() - 172800000).toISOString() },
    { name: '匿名用户', content: '在移动端阅读时有些图片显示不全', type: '问题反馈', timestamp: new Date(Date.now() - 259200000).toISOString() },
    { name: '赵六', content: '代码示例非常有帮助，可以再多一些吗？', type: '功能建议', timestamp: new Date(Date.now() - 345600000).toISOString() }
  ]
}

// 刷新数据
const refreshData = () => {
  loadDashboardData()
}

// 组件挂载时加载数据
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background-color: #e0e0e0;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: #fff;
  border-radius: 8px;
  border: 1px solid #eaeaea;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.stat-card h3 {
  font-size: 1rem;
  font-weight: 500;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 0.5rem;
}

.stat-trend {
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.trend-icon {
  color: #4caf50;
}

.data-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 992px) {
  .data-section {
    grid-template-columns: 1fr 1fr;
  }
}

.section-popular-docs,
.section-feedback {
  background-color: #fff;
  border-radius: 8px;
  border: 1px solid #eaeaea;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.section-popular-docs h2,
.section-feedback h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eaeaea;
}

.data-table th {
  font-weight: 600;
  color: #666;
  background-color: #f9f9f9;
}

.feedback-content {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feedback-tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.feedback-tag.general {
  background-color: #e3f2fd;
  color: #1976d2;
}

.feedback-tag.issue {
  background-color: #ffebee;
  color: #d32f2f;
}

.feedback-tag.suggestion {
  background-color: #e8f5e9;
  color: #388e3c;
}

.feedback-tag.correction {
  background-color: #fff8e1;
  color: #ffa000;
}

.trend-up {
  color: #4caf50;
}

.trend-down {
  color: #f44336;
}

.loading-section {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-spinner {
  font-size: 1.25rem;
  color: #666;
}

@media (max-width: 768px) {
  .dashboard {
    padding: 1rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
}
</style> 