import * as echarts from 'echarts'
import type { ChartData } from '@/types'

let chart: echarts.ECharts | null = null

export function useCharts() {
  const initChart = (elementId: string) => {
    const chartElement = document.getElementById(elementId)
    if (!chartElement) return
    
    chart = echarts.init(chartElement)
    
    // 监听窗口大小变化
    window.addEventListener('resize', () => {
      chart?.resize()
    })
  }
  
  const updateChart = (data: ChartData) => {
    if (!chart) return
    
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['访问量', '独立访客']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '访问量',
          type: 'line',
          smooth: true,
          data: data.visits,
          itemStyle: {
            color: '#18a058'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: 'rgba(24, 160, 88, 0.4)'
              },
              {
                offset: 1,
                color: 'rgba(24, 160, 88, 0.1)'
              }
            ])
          }
        },
        {
          name: '独立访客',
          type: 'line',
          smooth: true,
          data: data.visitors,
          itemStyle: {
            color: '#2080f0'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: 'rgba(32, 128, 240, 0.4)'
              },
              {
                offset: 1,
                color: 'rgba(32, 128, 240, 0.1)'
              }
            ])
          }
        }
      ]
    })
  }
  
  const destroyChart = () => {
    if (chart) {
      chart.dispose()
      chart = null
    }
    window.removeEventListener('resize', () => {
      chart?.resize()
    })
  }
  
  return {
    initChart,
    updateChart,
    destroyChart
  }
} 