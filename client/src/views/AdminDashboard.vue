<template>
  <div class="admin-dashboard">
    <h1 class="page-title">管理后台</h1>
    
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>正在加载数据...</p>
    </div>
    
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
      </div>
      <p>{{ error }}</p>
      <button @click="fetchDashboardData" class="retry-button">重试</button>
    </div>
    
    <div v-else class="dashboard-content">
      <!-- 数据概览 -->
      <section class="dashboard-section">
        <h2 class="section-title">数据概览</h2>
        <div class="stats-overview">
          <div class="stat-card">
            <div class="stat-icon visitors-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ dashboardData.visit_stats.unique_visitors }}</div>
              <div class="stat-label">访问人数</div>
              <div class="stat-period">过去{{ dashboardData.visit_stats.period_days }}天</div>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon views-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ dashboardData.visit_stats.total_visits }}</div>
              <div class="stat-label">总浏览量</div>
              <div class="stat-period">过去{{ dashboardData.visit_stats.period_days }}天</div>
            </div>
          </div>
          
          <div class="stat-card">
            <div class="stat-icon feedback-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ dashboardData.recent_feedback.length }}</div>
              <div class="stat-label">反馈数量</div>
              <div class="stat-period">最新反馈</div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 访问趋势图 -->
      <section class="dashboard-section">
        <h2 class="section-title">访问趋势</h2>
        <div class="visits-chart">
          <div class="chart-container">
            <!-- 这里可以使用echarts或其他图表库 -->
            <div class="placeholder-chart">
              <div class="chart-bars">
                <div v-for="(item, index) in dashboardData.visit_stats.daily_data" :key="index" 
                     class="chart-bar" 
                     :style="{ height: `${item.total_visits / 5}px` }">
                  <div class="bar-value">{{ item.total_visits }}</div>
                </div>
              </div>
              <div class="chart-labels">
                <div v-for="(item, index) in dashboardData.visit_stats.daily_data" :key="index" class="chart-label">
                  {{ formatDate(item.date) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <!-- 热门阅读 -->
      <section class="dashboard-section">
        <h2 class="section-title">热门阅读</h2>
        <div class="popular-docs">
          <table class="data-table">
            <thead>
              <tr>
                <th>排名</th>
                <th>标题</th>
                <th>访问量</th>
                <th>评分</th>
                <th>趋势</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(doc, index) in dashboardData.popular_docs" :key="doc.path">
                <td class="rank-cell">{{ index + 1 }}</td>
                <td class="title-cell">
                  <router-link :to="`/docs/${doc.path}`">{{ doc.title }}</router-link>
                </td>
                <td class="visits-cell">{{ doc.visits }}</td>
                <td class="rating-cell">
                  <div class="rating">
                    <span class="stars">★★★★★</span>
                    <span class="rating-value">{{ doc.avg_rating }}</span>
                  </div>
                </td>
                <td class="trend-cell">
                  <span :class="['trend-value', doc.last_week_trend > 0 ? 'trend-up' : 'trend-down']">
                    {{ formatTrend(doc.last_week_trend) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      
      <!-- 用户反馈 -->
      <section class="dashboard-section">
        <h2 class="section-title">用户反馈</h2>
        <div class="feedback-list">
          <table class="data-table">
            <thead>
              <tr>
                <th>用户</th>
                <th>类型</th>
                <th>内容</th>
                <th>联系方式</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(feedback, index) in dashboardData.recent_feedback" :key="index">
                <td>{{ feedback.name || '匿名用户' }}</td>
                <td>
                  <span :class="['feedback-type', `type-${feedback.type}`]">
                    {{ getFeedbackTypeName(feedback.type) }}
                  </span>
                </td>
                <td class="feedback-content">{{ feedback.content }}</td>
                <td>{{ feedback.contact || '未提供' }}</td>
                <td>{{ formatDateTime(feedback.timestamp) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { adminAPI } from '../services/api';

const loading = ref(true);
const error = ref(null);
const dashboardData = ref({
  popular_docs: [],
  visit_stats: { 
    daily_data: [],
    total_visits: 0,
    avg_visits: 0,
    unique_visitors: 0,
    period_days: 7
  },
  recent_feedback: []
});

// 格式化日期为短格式（MM-DD）
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}-${date.getDate()}`;
};

// 格式化完整日期时间
const formatDateTime = (dateTimeStr) => {
  if (!dateTimeStr) return '未知时间';
  
  const date = new Date(dateTimeStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 格式化趋势数据
const formatTrend = (trendValue) => {
  const percentage = (trendValue * 100).toFixed(1);
  const prefix = trendValue > 0 ? '+' : '';
  return `${prefix}${percentage}%`;
};

// 获取反馈类型名称
const getFeedbackTypeName = (type) => {
  const typeMap = {
    'bug': '问题反馈',
    'suggestion': '功能建议',
    'content': '内容反馈',
    'praise': '表扬',
    'other': '其他'
  };
  
  return typeMap[type] || type;
};

// 获取仪表盘数据
const fetchDashboardData = async () => {
  loading.value = true;
  error.value = null;
  
  try {
    const response = await adminAPI.getDashboard();
    dashboardData.value = response.data;
  } catch (err) {
    console.error('获取仪表盘数据失败:', err);
    error.value = '获取仪表盘数据失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchDashboardData();
});
</script>

<style scoped>
.admin-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 2rem;
  color: var(--color-text-primary);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top-color: var(--color-primary);
  animation: spin 1s ease-in-out infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--color-error);
}

.error-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
}

.retry-button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: var(--color-primary);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dashboard-section {
  background-color: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: var(--color-text-primary);
}

/* 数据概览卡片 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-card {
  background-color: var(--color-bg-primary);
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.visitors-icon {
  background-color: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
}

.views-icon {
  background-color: rgba(16, 185, 129, 0.1);
  color: rgb(16, 185, 129);
}

.feedback-icon {
  background-color: rgba(245, 158, 11, 0.1);
  color: rgb(245, 158, 11);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-text-primary);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.stat-period {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 0.25rem;
}

/* 访问趋势图 */
.visits-chart {
  background-color: var(--color-bg-primary);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.chart-container {
  height: 300px;
}

.placeholder-chart {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 0 1rem;
}

.chart-bar {
  width: 30px;
  background-color: var(--color-primary);
  border-radius: 4px 4px 0 0;
  margin: 0 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.bar-value {
  position: absolute;
  top: -20px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.chart-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  padding: 0 1rem;
}

.chart-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  width: 30px;
  text-align: center;
  margin: 0 4px;
}

/* 数据表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-bg-primary);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.data-table th {
  text-align: left;
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  font-weight: 600;
  color: var(--color-text-secondary);
}

.data-table td {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-primary);
}

.rank-cell {
  font-weight: bold;
  text-align: center;
  width: 60px;
}

.title-cell a {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}

.title-cell a:hover {
  text-decoration: underline;
}

.visits-cell {
  text-align: center;
}

.rating-cell {
  text-align: center;
}

.rating {
  display: inline-flex;
  align-items: center;
}

.stars {
  color: gold;
  margin-right: 0.5rem;
}

.trend-cell {
  text-align: center;
}

.trend-up {
  color: rgb(16, 185, 129);
}

.trend-down {
  color: rgb(239, 68, 68);
}

.feedback-type {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.type-bug {
  background-color: rgba(239, 68, 68, 0.1);
  color: rgb(239, 68, 68);
}

.type-suggestion {
  background-color: rgba(59, 130, 246, 0.1);
  color: rgb(59, 130, 246);
}

.type-content {
  background-color: rgba(16, 185, 129, 0.1);
  color: rgb(16, 185, 129);
}

.type-praise {
  background-color: rgba(245, 158, 11, 0.1);
  color: rgb(245, 158, 11);
}

.type-other {
  background-color: rgba(107, 114, 128, 0.1);
  color: rgb(107, 114, 128);
}

.feedback-content {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .admin-dashboard {
    padding: 1rem;
  }
  
  .stats-overview {
    grid-template-columns: 1fr;
  }
  
  .data-table {
    display: block;
    overflow-x: auto;
  }
}
</style> 