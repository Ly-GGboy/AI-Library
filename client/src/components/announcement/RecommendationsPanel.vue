<template>
  <div class="tab-content-container">
    <h3 class="panel-title">内容推荐</h3>
    
    <div v-if="loading" class="panel-loading">
      <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent rounded-full"></span>
      <span>加载中...</span>
    </div>
    
    <div v-else-if="error" class="panel-error">
      <ExclamationCircleIcon class="error-icon" />
      {{ error }}
    </div>
    
    <div v-else-if="!recommendations || recommendations.length === 0" class="panel-empty">
      暂无推荐内容
    </div>
    
    <div v-else class="recommendations-list">
      <div 
        v-for="(item, index) in recommendations" 
        :key="index" 
        class="recommendation-item"
      >
        <div class="recommendation-header">
          <div class="type-badge">{{ item.type }}</div>
        </div>
        
        <h3 class="recommendation-title">{{ item.title }}</h3>
        
        <p class="recommendation-description">{{ item.description }}</p>
        
        <div v-if="item.tags && item.tags.length > 0" class="recommendation-tags">
          <span v-for="(tag, tagIndex) in item.tags" :key="tagIndex" class="tag">
            <TagIcon class="tag-icon" />
            {{ tag }}
          </span>
        </div>
        
        <a 
          v-if="item.link" 
          :href="String(item.link).startsWith('http') ? item.link : `/#${item.link}`" 
          class="recommendation-link"
          :target="String(item.link).startsWith('http') ? '_blank' : '_self'"
        >
          了解更多
          <ArrowRightIcon class="link-icon" />
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';
import { ArrowRightIcon, ExclamationCircleIcon, TagIcon } from '@heroicons/vue/24/outline';

interface Recommendation {
  title: string;
  description: string;
  type: string;
  link: string;
  tags?: string[];
}

const props = defineProps({
  recommendations: {
    type: Array as () => Recommendation[],
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
</script>

<style scoped>
.panel-title {
  @apply text-lg font-bold mb-4 text-gray-900 dark:text-gray-100;
}

.panel-loading {
  @apply flex items-center space-x-2 justify-center text-gray-500 text-sm py-10;
}

.panel-error {
  @apply flex items-center space-x-2 text-red-500 bg-red-50 dark:bg-red-900/20 p-4 rounded-md;
}

.error-icon {
  @apply w-5 h-5 flex-shrink-0;
}

.panel-empty {
  @apply text-center text-gray-500 py-10;
}

.recommendations-list {
  @apply space-y-6 max-h-[calc(80vh-120px)] overflow-y-auto pr-2;
}

.recommendation-item {
  @apply bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm transition duration-300;
  @apply hover:shadow-md;
}

.recommendation-header {
  @apply flex items-center justify-between mb-2;
}

.type-badge {
  @apply bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 px-2 py-0.5 rounded text-xs font-medium;
}

.recommendation-title {
  @apply text-lg font-bold text-gray-800 dark:text-gray-200 mb-2;
}

.recommendation-description {
  @apply text-gray-600 dark:text-gray-400 text-sm mb-3;
}

.recommendation-tags {
  @apply flex flex-wrap gap-2 mb-3;
}

.tag {
  @apply inline-flex items-center bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-0.5 rounded text-xs;
}

.tag-icon {
  @apply w-3 h-3 mr-1 text-gray-500 dark:text-gray-400;
}

.recommendation-link {
  @apply inline-flex items-center text-primary-600 dark:text-primary-400 text-sm font-medium hover:text-primary-700 dark:hover:text-primary-300 transition-colors duration-200;
}

.link-icon {
  @apply w-4 h-4 ml-1;
}
</style> 