<template>
  <div class="tab-content-container">
    <div class="panel-header">
      <h3 class="panel-title">最新更新</h3>
      
      <div v-if="loading" class="panel-status">
        <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent rounded-full mr-1"></span>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="error" class="panel-status panel-error">
        <ExclamationCircleIcon class="error-icon" />
        {{ error }}
      </div>
      
      <div v-else-if="!sortedUpdates || sortedUpdates.length === 0" class="panel-status">
        暂无更新信息
      </div>
    </div>
    
    <div v-if="sortedUpdates && sortedUpdates.length > 0" class="updates-list">
      <div 
        v-for="(update, index) in sortedUpdates" 
        :key="index" 
        class="update-item"
        :class="{ 'important': update.important }"
      >
        <div class="update-header">
          <div class="version-badge">{{ update.version }}</div>
          <div class="update-date">{{ formatDate(update.date) }}</div>
        </div>
        
        <h3 class="update-title">
          <span v-if="update.important" class="important-badge">重要</span>
          {{ update.title }}
        </h3>
        
        <p class="update-content">{{ update.content }}</p>
        
        <ul v-if="update.changes && update.changes.length > 0" class="changes-list">
          <li v-for="(change, cIndex) in update.changes" :key="cIndex" class="change-item">
            <CheckCircleIcon class="change-icon" />
            <span>{{ change }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineProps, computed } from 'vue';
import { CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/vue/24/outline';

interface Update {
  version: string;
  date: string;
  title: string;
  content: string;
  changes?: string[];
  important?: boolean;
}

const props = defineProps({
  updates: {
    type: Array as () => Update[],
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
});

// 确保更新按时间倒序排列
const sortedUpdates = computed(() => {
  if (!props.updates || props.updates.length === 0) return [];
  return [...props.updates].sort((a, b) => {
    return new Date(b.date).getTime() - new Date(a.date).getTime();
  });
});

const formatDate = (dateString: string): string => {
  if (!dateString) return '未知日期';
  
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (e) {
    console.error('Date formatting error:', e);
    return '日期格式错误';
  }
};

onMounted(() => {
  // 任何初始化逻辑
});
</script>

<style scoped>
.panel-header {
  @apply flex items-center justify-between mb-4;
}

.panel-title {
  @apply text-lg font-bold text-gray-900 dark:text-gray-100;
}

.panel-status {
  @apply flex items-center text-gray-500 text-sm;
}

.panel-error {
  @apply text-red-500;
}

.error-icon {
  @apply w-4 h-4 flex-shrink-0 mr-1;
}

.updates-list {
  @apply space-y-6 max-h-[calc(80vh-120px)] overflow-y-auto pr-2;
}

.update-item {
  @apply bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm transition duration-300;
  @apply border-l-4 border-primary-500 dark:border-primary-400;
  @apply hover:shadow-md;
}

.update-item.important {
  @apply border-l-4 border-blue-400 dark:border-blue-500;
  @apply bg-blue-50 dark:bg-blue-900/20;
}

.update-header {
  @apply flex items-center justify-between mb-2;
}

.version-badge {
  @apply bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded-md text-xs font-medium;
}

.update-date {
  @apply text-xs text-gray-500 dark:text-gray-400;
}

.update-title {
  @apply text-lg font-bold text-gray-800 dark:text-gray-200 mb-2 flex items-center;
}

.important-badge {
  @apply bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 text-xs px-2 py-0.5 rounded mr-2;
}

.update-content {
  @apply text-gray-600 dark:text-gray-400 text-sm mb-3;
}

.changes-list {
  @apply text-sm text-gray-700 dark:text-gray-300 space-y-2 mt-2;
}

.change-item {
  @apply flex items-start space-x-2;
}

.change-icon {
  @apply w-4 h-4 text-green-500 dark:text-green-400 mt-0.5 flex-shrink-0;
}
</style> 