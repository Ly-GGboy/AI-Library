<template>
  <div class="feedback-view">
    <!-- 页面标题 -->
    <n-page-header>
      <template #title>
        <n-space align="center">
          <n-icon size="24">
            <message-outline />
          </n-icon>
          <span>用户反馈管理</span>
        </n-space>
      </template>
      <template #extra>
        <n-button
          type="primary"
          :loading="loading"
          @click="refreshFeedback"
        >
          刷新数据
        </n-button>
      </template>
    </n-page-header>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="12" class="stats-grid">
      <n-grid-item>
        <n-card>
          <n-statistic label="总反馈数">
            <n-number-animation
              ref="totalAnimation"
              :from="0"
              :to="getFeedbackStats.total"
            />
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="问题反馈">
            <n-number-animation
              ref="issuesAnimation"
              :from="0"
              :to="getFeedbackStats.issues"
            />
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="功能建议">
            <n-number-animation
              ref="suggestionsAnimation"
              :from="0"
              :to="getFeedbackStats.suggestions"
            />
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="其他反馈">
            <n-number-animation
              ref="othersAnimation"
              :from="0"
              :to="getFeedbackStats.others"
            />
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 筛选和操作区 -->
    <n-card class="filter-card">
      <n-space align="center" justify="space-between">
        <n-space>
          <n-select
            v-model:value="selectedType"
            :options="typeOptions"
            placeholder="选择反馈类型"
            clearable
          />
          <n-select
            v-model:value="sortOrder"
            :options="sortOptions"
            placeholder="排序方式"
          />
        </n-space>
        <n-space>
          <n-button
            :disabled="!checkedRowKeys.length"
            @click="handleBatchReply"
          >
            批量回复
          </n-button>
        </n-space>
      </n-space>
    </n-card>

    <!-- 数据表格 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="filteredFeedback"
        :loading="loading"
        :pagination="pagination"
        :row-key="rowKey"
        @update:checked-row-keys="handleCheck"
      />
    </n-card>

    <!-- 详情抽屉 -->
    <n-drawer
      v-model:show="showDrawer"
      :width="500"
      placement="right"
    >
      <n-drawer-content
        v-if="selectedFeedback"
        :title="selectedFeedback.replied ? '反馈详情' : '回复反馈'"
        :native-scrollbar="false"
      >
        <n-descriptions :column="1" bordered>
          <n-descriptions-item label="用户">
            {{ selectedFeedback.name || '匿名用户' }}
          </n-descriptions-item>
          <n-descriptions-item label="反馈内容">
            {{ selectedFeedback.content }}
          </n-descriptions-item>
          <n-descriptions-item label="反馈类型">
            <n-tag
              :type="getFeedbackTypeTag(selectedFeedback.type)"
              round
              size="small"
            >
              {{ selectedFeedback.type || '一般反馈' }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="提交时间">
            {{ formatDate(selectedFeedback.timestamp) }}
          </n-descriptions-item>
          <n-descriptions-item
            v-if="selectedFeedback.replied"
            label="回复内容"
          >
            {{ selectedFeedback.reply }}
          </n-descriptions-item>
          <n-descriptions-item
            v-if="selectedFeedback.replied && selectedFeedback.replyTimestamp"
            label="回复时间"
          >
            {{ formatDate(selectedFeedback.replyTimestamp) }}
          </n-descriptions-item>
        </n-descriptions>

        <!-- 回复表单 -->
        <template v-if="!selectedFeedback.replied">
          <div class="reply-form">
            <n-input
              v-model:value="replyContent"
              type="textarea"
              placeholder="请输入回复内容"
              :rows="4"
            />
            <n-space justify="end" class="reply-actions">
              <n-button
                @click="showDrawer = false"
              >
                取消
              </n-button>
              <n-button
                type="primary"
                :loading="replying"
                :disabled="!replyContent.trim()"
                @click="handleReply"
              >
                提交回复
              </n-button>
            </n-space>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import {
  useMessage,
  NTag,
  NEllipsis,
  NSpace,
  NButton,
  NPageHeader,
  NIcon,
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NNumberAnimation,
  NSelect,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NDescriptions,
  NDescriptionsItem,
  NInput
} from 'naive-ui'
import { adminAPI } from '@/services/api'
import { formatDate } from '@/utils/date'
import { ChatboxOutline } from '@vicons/ionicons5'
import {
  ChatMultiple20Regular,
  ArrowClockwise20Regular,
  Chat20Regular,
  Bug20Regular,
  Lightbulb20Regular,
  Edit20Regular
} from '@vicons/fluent'

interface FeedbackItem {
  id: string
  name: string
  content: string
  type: string
  replied: boolean
  timestamp: string
  reply?: string
  replyTimestamp?: string
}

// 创建消息实例
const message = useMessage()

// 组件状态
const loading = ref(false)
const replying = ref(false)
const showDrawer = ref(false)
const feedbackList = ref<FeedbackItem[]>([])
const selectedType = ref(null)
const sortOrder = ref('desc')
const selectedFeedback = ref<FeedbackItem | null>(null)
const checkedRowKeys = ref<string[]>([])
const replyContent = ref('')

// 类型选项
const typeOptions = [
  { label: '问题', value: '问题' },
  { label: '建议', value: '建议' },
  { label: '其他', value: '其他' }
]

// 排序选项
const sortOptions = [
  { label: '最新优先', value: 'desc' },
  { label: '最早优先', value: 'asc' }
]

// 分页配置
const pagination = {
  pageSize: 10
}

// 获取反馈统计数据
const getFeedbackStats = computed(() => {
  return {
    total: feedbackList.value.length,
    issues: getFeedbackCountByType('问题'),
    suggestions: getFeedbackCountByType('建议'),
    others: getFeedbackCountByType('其他')
  }
})

// 获取指定类型的反馈数量
const getFeedbackCountByType = (type: string) => {
  return feedbackList.value.filter(item => item.type === type).length
}

// 刷新反馈数据
const refreshFeedback = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getFeedback()
    feedbackList.value = response.data
    message.success('数据已更新')
  } catch (error) {
    message.error('获取数据失败')
    console.error('获取反馈数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 批量回复
const handleBatchReply = () => {
  message.info('批量回复功能开发中')
}

// 提交回复
const handleReply = async () => {
  if (!selectedFeedback.value || !replyContent.value.trim()) return

  replying.value = true
  try {
    await adminAPI.replyToFeedback(selectedFeedback.value.id, replyContent.value)
    message.success('回复成功')
    showDrawer.value = false
    replyContent.value = ''
    await refreshFeedback()
  } catch (error) {
    message.error('回复失败')
    console.error('回复反馈失败:', error)
  } finally {
    replying.value = false
  }
}

// 初始化数据
onMounted(() => {
  refreshFeedback()
})

// 表格列定义
const columns = [
  {
    type: 'selection',
    disabled: (row: FeedbackItem) => row.replied
  },
  {
    title: '用户',
    key: 'name',
    width: 120,
    ellipsis: true,
    render: (row: FeedbackItem) => row.name || '匿名用户'
  },
  {
    title: '反馈内容',
    key: 'content',
    ellipsis: true,
    render: (row: FeedbackItem) => {
      return h(
        NEllipsis,
        {
          style: 'max-width: 400px',
          tooltip: { width: 'trigger' }
        },
        { default: () => row.content }
      )
    }
  },
  {
    title: '类型',
    key: 'type',
    width: 100,
    render: (row: FeedbackItem) => {
      return h(
        NTag,
        {
          type: getFeedbackTypeTag(row.type),
          round: true,
          size: 'small'
        },
        { default: () => row.type || '一般反馈' }
      )
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: FeedbackItem) => {
      return h(
        NTag,
        {
          type: row.replied ? 'success' : 'warning',
          round: true,
          size: 'small'
        },
        { default: () => row.replied ? '已回复' : '待处理' }
      )
    }
  },
  {
    title: '提交时间',
    key: 'timestamp',
    width: 180,
    render: (row: FeedbackItem) => formatDate(row.timestamp)
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    render: (row: FeedbackItem) => {
      return h(
        NSpace,
        { align: 'center' },
        {
          default: () => [
            h(
              NButton,
              {
                size: 'small',
                quaternary: true,
                type: 'primary',
                onClick: () => viewFeedback(row)
              },
              { default: () => '查看' }
            ),
            !row.replied &&
              h(
                NButton,
                {
                  size: 'small',
                  quaternary: true,
                  type: 'info',
                  onClick: () => handleReplyClick(row)
                },
                { default: () => '回复' }
              )
          ]
        }
      )
    }
  }
] as DataTableColumns<FeedbackItem>

// 计算属性：过滤后的反馈列表
const filteredFeedback = computed(() => {
  let result = [...feedbackList.value]
  
  if (selectedType.value) {
    result = result.filter(item => item.type === selectedType.value)
  }
  
  result.sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime()
    const timeB = new Date(b.timestamp).getTime()
    return sortOrder.value === 'desc' ? timeB - timeA : timeA - timeB
  })
  
  return result
})

// 获取反馈类型对应的标签类型
function getFeedbackTypeTag(type: string): 'default' | 'error' | 'primary' | 'success' | 'info' | 'warning' {
  switch (type) {
    case '建议':
      return 'primary'
    case '问题':
      return 'error'
    case '其他':
      return 'info'
    default:
      return 'default'
  }
}

// 行数据的唯一键
const rowKey = (row: FeedbackItem) => row.id

// 查看反馈详情
const viewFeedback = (feedback: FeedbackItem) => {
  selectedFeedback.value = feedback
  showDrawer.value = true
}

// 处理回复点击
const handleReplyClick = (feedback: FeedbackItem) => {
  selectedFeedback.value = feedback
  showDrawer.value = true
  replyContent.value = ''
}

// 处理选中行变化
const handleCheck = (keys: (string | number)[]) => {
  checkedRowKeys.value = keys.map(key => String(key))
}
</script>

<style scoped>
.feedback-view {
  padding: 16px;
}

.stats-grid {
  margin: 16px 0;
}

.filter-card {
  margin-bottom: 16px;
}

.reply-form {
  margin-top: 24px;
}

.reply-actions {
  margin-top: 16px;
}
</style> 