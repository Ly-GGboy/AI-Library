<template>
  <div class="stats-view">
    <n-card>
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <n-h2>
              <n-icon size="24" class="mr-2">
                <ChartMultiple20Regular />
              </n-icon>
              访问统计
            </n-h2>
            <n-text depth="3" class="subtitle">
              实时监控网站访问数据和用户行为
            </n-text>
          </div>
          <div class="header-right">
            <n-button
              @click="refreshData"
              :loading="loading"
              type="primary"
              secondary
              round
            >
              <template #icon>
                <n-icon><ArrowClockwise20Regular /></n-icon>
              </template>
              刷新数据
            </n-button>
          </div>
        </div>
      </template>

      <!-- 统计卡片 -->
      <n-grid :x-gap="12" :y-gap="8" :cols="4">
        <n-grid-item v-for="(card, index) in statCards" :key="index">
          <n-card :class="['stat-card', card.type]" size="small">
            <div class="stat-card-content">
              <div class="stat-info">
                <n-statistic :value="card.value" :precision="0">
                  <template #prefix>
                    <n-icon :size="24" :class="card.type">
                      <component :is="card.icon" />
                    </n-icon>
                  </template>
                </n-statistic>
                <n-text depth="3">{{ card.label }}</n-text>
              </div>
              <div class="stat-trend" v-if="card.trend !== undefined">
                <n-tag :type="card.trend >= 0 ? 'success' : 'error'" size="small">
                  {{ card.trend >= 0 ? '↑' : '↓' }} {{ Math.abs(card.trend).toFixed(1) }}%
                </n-tag>
                <n-text depth="3" size="small">较上周</n-text>
              </div>
            </div>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- 过滤器 -->
      <div class="filter-section">
        <n-space align="center">
          <n-select
            v-model:value="timeRange"
            :options="timeRangeOptions"
            size="small"
            style="width: 120px"
          />
          <n-date-picker
            v-model:value="customDateRange"
            type="daterange"
            size="small"
            :disabled="timeRange !== 'custom'"
            style="width: 250px"
          />
        </n-space>
      </div>

      <!-- 访问趋势图表 -->
      <div class="chart-section">
        <n-card title="访问趋势" size="small">
          <template #header-extra>
            <n-space>
              <n-radio-group v-model:value="chartType" size="small">
                <n-radio-button value="daily">日</n-radio-button>
                <n-radio-button value="weekly">周</n-radio-button>
                <n-radio-button value="monthly">月</n-radio-button>
              </n-radio-group>
            </n-space>
          </template>
          <div ref="chartRef" style="width: 100%; height: 300px"></div>
        </n-card>
      </div>

      <!-- 访问明细表格 -->
      <div class="table-section">
        <n-card title="访问明细" size="small">
          <n-data-table
            :columns="columns"
            :data="tableData"
            :pagination="pagination"
            :loading="loading"
            striped
          />
        </n-card>
      </div>

      <!-- 添加图表容器 -->
      <div id="visitChart" class="chart-container"></div>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h } from 'vue'
import { useMessage } from 'naive-ui'
import { adminAPI } from '@/services/api'
import * as echarts from 'echarts'
import {
  ChartMultiple20Regular,
  ArrowClockwise20Regular,
  People20Regular,
  Eye20Regular,
  Timer20Regular,
  ArrowTrendingLines20Regular
} from '@vicons/fluent'
import type { VisitStats, DailyStats } from '@/types'
import { useCharts } from '@/composables/useCharts'

// 创建消息实例
const message = useMessage()

// 状态
const loading = ref(false)
const stats = ref<VisitStats | null>(null)
const timeRange = ref('7d')
const customDateRange = ref<[number, number]>([
  Date.now() - 7 * 24 * 60 * 60 * 1000,
  Date.now()
])
const chartType = ref('daily')
const refreshTimer = ref<number | null>(null)

// 图表相关
const { initChart, updateChart, destroyChart } = useCharts()

// 时间范围选项
const timeRangeOptions = [
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '最近90天', value: '90d' },
  { label: '自定义', value: 'custom' }
]

// 表格列定义
const columns = [
  {
    title: '日期',
    key: 'date',
    width: 120,
    fixed: 'left'
  },
  {
    title: '访问量',
    key: 'total_visits',
    width: 100,
    sorter: 'default'
  },
  {
    title: '独立访客',
    key: 'unique_visitors',
    width: 100
  },
  {
    title: '同比变化',
    key: 'change_rate',
    width: 120,
    render: (row: any) => {
      const value = row.change_rate || 0
      const color = value >= 0 ? '#18a058' : '#d03050'
      return h(
        'div',
        {
          style: {
            color: color
          }
        },
        `${value >= 0 ? '↑' : '↓'} ${Math.abs(value * 100).toFixed(1)}%`
      )
    }
  },
  {
    title: '平均停留时间',
    key: 'avg_duration',
    width: 120
  },
  {
    title: '跳出率',
    key: 'bounce_rate',
    width: 100,
    render: (row: any) => `${row.bounce_rate || 0}%`
  }
]

// 表格数据
const tableData = computed(() => {
  return stats.value?.daily_data || []
})

// 分页配置
const pagination = {
  pageSize: 10
}

// 获取统计数据
const fetchStats = async () => {
  try {
    loading.value = true
    const data = await adminAPI.getStats()
    stats.value = data.stats
    updateChartData()
  } catch (error) {
    message.error('获取统计数据失败')
    console.error('获取统计数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  fetchStats()
}

// 更新图表数据
const updateChartData = () => {
  if (!stats.value) return
  
  const chartData = {
    dates: stats.value.daily_data.map((item: DailyStats) => item.date),
    visits: stats.value.daily_data.map((item: DailyStats) => item.total_visits),
    visitors: stats.value.daily_data.map((item: DailyStats) => item.unique_visitors)
  }
  
  updateChart(chartData)
}

// 计算统计卡片数据
const statCards = computed(() => {
  if (!stats.value) return []
  
  return [
    {
      label: '总访问量',
      value: stats.value.total_visits,
      icon: Eye20Regular,
      type: 'visits',
      trend: 14 // 示例数据
    },
    {
      label: '独立访客',
      value: stats.value.unique_visitors,
      icon: People20Regular,
      type: 'visitors',
      trend: 10
    },
    {
      label: '日均访问',
      value: Math.round(stats.value.avg_daily_visits),
      icon: Timer20Regular,
      type: 'daily',
      trend: 3
    },
    {
      label: '跳出率',
      value: stats.value.bounce_rate,
      icon: ArrowTrendingLines20Regular,
      type: 'bounce',
      trend: -1
    }
  ]
})

// 生命周期钩子
onMounted(() => {
  fetchStats()
  initChart('visitChart')
  // 每5分钟自动刷新一次
  refreshTimer.value = window.setInterval(fetchStats, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
  destroyChart()
})
</script>

<style scoped>
.stats-view {
  min-height: 100%;
  background: transparent;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subtitle {
  margin-left: 32px;
}

.stat-card {
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.stat-card-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-section {
  margin: 16px 0;
  padding: 16px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.chart-section {
  margin-bottom: 16px;
}

.visits {
  color: var(--primary-color);
}

.visitors {
  color: var(--info-color);
}

.daily {
  color: var(--warning-color);
}

.bounce {
  color: var(--error-color);
}

:deep(.n-card) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px);
  transition: all 0.3s ease;
}

:deep(.n-card:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.chart-container {
  margin-top: 16px;
  height: 400px;
  width: 100%;
}
</style> 