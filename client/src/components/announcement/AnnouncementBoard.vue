<template>
  <Transition 
    name="announcement-fade"
    appear
    @before-enter="beforeEnter"
    @enter="enter"
    @leave="leave"
  >
    <div v-if="isVisible" class="announcement-overlay" @click.self="closeBoard">
      <div class="announcement-board" ref="boardRef">
        <div class="announcement-header">
          <h2 class="announcement-title">公告与反馈</h2>
          <button class="close-button" @click="closeBoard" aria-label="关闭">
            <XMarkIcon class="h-6 w-6" />
          </button>
        </div>
        
        <div class="announcement-tabs">
          <button 
            class="tab-button" 
            :class="{ 'active': activeTab === 'updates' }"
            @click="activeTab = 'updates'"
          >
            <ClockIcon class="w-4 h-4 mr-1" />
            更新动态
          </button>
          <button 
            class="tab-button" 
            :class="{ 'active': activeTab === 'recommendations' }"
            @click="activeTab = 'recommendations'"
          >
            <BookmarkIcon class="w-4 h-4 mr-1" />
            内容推荐
          </button>
          <button 
            class="tab-button" 
            :class="{ 'active': activeTab === 'feedback' }"
            @click="activeTab = 'feedback'"
          >
            <ChatBubbleLeftRightIcon class="w-4 h-4 mr-1" />
            用户反馈
          </button>
        </div>
        
        <div class="announcement-content">
          <Transition name="tab-transition" mode="out-in">
            <component 
              :is="currentTabComponent" 
              :updates="updates" 
              :recommendations="recommendations" 
              :submitting="submitting" 
              :error="error" 
              :success="success" 
              @submit="submitFeedback" />
          </Transition>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { XMarkIcon, ClockIcon, BookmarkIcon, ChatBubbleLeftRightIcon } from '@heroicons/vue/24/outline'
import { useAnnouncementStore } from '../../stores/announcement'
import UpdatesPanel from './UpdatesPanel.vue'
import RecommendationsPanel from './RecommendationsPanel.vue'
import FeedbackForm from './FeedbackForm.vue'
import gsap from 'gsap'

const announcementStore = useAnnouncementStore()
const isVisible = ref(false)
const activeTab = ref('updates')
const submitting = ref(false)
const error = ref('')
const success = ref('')
const boardRef = ref<HTMLElement | null>(null)

// 使用计算属性动态确定当前显示的组件
const currentTabComponent = computed(() => {
  // 确保组件正确引用
  switch(activeTab.value) {
    case 'updates': return UpdatesPanel;
    case 'recommendations': return RecommendationsPanel;
    case 'feedback': return FeedbackForm;
    default: return UpdatesPanel; // 默认返回更新面板
  }
})

// 确保updates和recommendations有默认值
const updates = ref<any[]>([{
  version: "1.0.0",
  date: new Date().toISOString(),
  title: "加载中...",
  content: "正在获取更新信息..."
}]);

const recommendations = ref<any[]>([{
  title: "加载中...",
  description: "正在获取推荐内容...",
  type: "系统",
  link: ""
}]);

// 苹果风格动画
const beforeEnter = (el: Element): void => {
  (el as HTMLElement).style.opacity = '0'
}

const enter = (el: Element, done: () => void): void => {
  gsap.to(el, {
    opacity: 1,
    duration: 0.3,
    ease: 'power2.out',
    onComplete: done
  })
  
  if (boardRef.value) {
    gsap.fromTo(
      boardRef.value,
      { scale: 0.9, opacity: 0, y: 20 },
      { 
        scale: 1, 
        opacity: 1, 
        y: 0, 
        duration: 0.4, 
        ease: 'back.out(1.7)',
        delay: 0.1
      }
    )
  }
}

const leave = (el: Element, done: () => void): void => {
  gsap.to(el, {
    opacity: 0,
    duration: 0.3,
    ease: 'power2.in',
    onComplete: done
  })
  
  if (boardRef.value) {
    gsap.to(boardRef.value, {
      scale: 0.9,
      opacity: 0,
      y: 20,
      duration: 0.25,
      ease: 'back.in(1.7)'
    })
  }
}

const openBoard = (): void => {
  isVisible.value = true
  
  // 每次打开公告板时加载最新数据
  Promise.all([
    loadUpdates(),
    loadRecommendations()
  ]).catch(err => {
    console.error('Error loading announcement data:', err)
  })
}

const closeBoard = (): void => {
  isVisible.value = false
  // 重置表单状态
  error.value = ''
  success.value = ''
}

const loadUpdates = async (): Promise<void> => {
  try {
    const fetchedUpdates = await announcementStore.getUpdates();
    if (Array.isArray(fetchedUpdates) && fetchedUpdates.length > 0) {
      updates.value = fetchedUpdates.map(update => ({
        version: update.id || "未知版本",
        date: update.date || new Date().toISOString(),
        title: update.title || "未知更新",
        content: update.description || "暂无详细内容",
        changes: update.changes || [],
        important: update.important || false
      }));
    } else {
      // 如果返回空数据，设置一个提示信息
      updates.value = [{
        version: "提示",
        date: new Date().toISOString(),
        title: "暂无更新",
        content: "系统暂时没有新的更新信息",
        changes: [],
        important: false
      }];
    }
  } catch (err) {
    console.error('Failed to load updates:', err);
    // 设置错误状态的数据
    updates.value = [{
      version: "错误",
      date: new Date().toISOString(),
      title: "加载失败",
      content: "无法获取更新信息，请稍后再试。",
      changes: [],
      important: false
    }];
  }
};

const loadRecommendations = async (): Promise<void> => {
  try {
    const fetchedRecommendations = await announcementStore.getRecommendations();
    if (Array.isArray(fetchedRecommendations) && fetchedRecommendations.length > 0) {
      recommendations.value = fetchedRecommendations.map(rec => ({
        title: rec.title || "未知推荐",
        description: rec.description || "暂无描述",
        type: rec.category || "一般",
        link: rec.path || rec.url || "",
        tags: rec.tags || []
      }));
    } else {
      // 如果返回空数据，设置一个提示信息
      recommendations.value = [{
        title: "暂无推荐",
        description: "系统暂时没有新的内容推荐",
        type: "提示",
        link: "",
        tags: []
      }];
    }
  } catch (err) {
    console.error('Failed to load recommendations:', err);
    // 设置错误状态的数据
    recommendations.value = [{
      title: "加载失败",
      description: "无法获取推荐内容，请稍后再试。",
      type: "错误",
      link: "",
      tags: []
    }];
  }
};

const submitFeedback = async (feedback: any): Promise<void> => {
  submitting.value = true
  error.value = ''
  success.value = ''
  
  try {
    // 调用实际的API接口
    await announcementStore.submitFeedback(feedback)
    
    // 将反馈内容记录到控制台，供开发者查看
    console.info('收到用户反馈:', feedback)
    
    // 返回成功信息
    success.value = '感谢您的反馈，我们会认真考虑您的建议！'
  } catch (err) {
    error.value = '提交反馈失败，请稍后再试'
    console.error('提交反馈出错:', err)
  } finally {
    submitting.value = false
  }
}

// 暴露方法给父组件调用
defineExpose({
  openBoard,
  closeBoard
})

onMounted(() => {
  // 初始加载
  loadUpdates().catch(err => {
    console.error('Failed to load updates:', err);
    updates.value = [{
      version: "错误",
      date: new Date().toISOString(),
      title: "加载失败",
      content: "无法获取更新信息，请稍后再试。"
    }];
  });
  
  loadRecommendations().catch(err => {
    console.error('Failed to load recommendations:', err);
    recommendations.value = [{
      title: "加载失败",
      description: "无法获取推荐内容，请稍后再试。",
      type: "错误",
      link: "",
      tags: []
    }];
  });
})
</script>

<style scoped>
.announcement-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow-y: auto;
  padding: 20px;
}

.announcement-board {
  @apply bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-3xl mx-4 flex flex-col overflow-hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  will-change: transform, opacity;
  /* 设置固定的最小高度，确保公告板尺寸稳定 */
  min-height: 500px;
  /* 设置固定的高度，但允许内容区域滚动 */
  height: 70vh;
}

.announcement-header {
  @apply flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700;
}

.announcement-title {
  @apply text-xl font-bold text-gray-900 dark:text-gray-100;
}

.close-button {
  @apply text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 p-1;
}

.announcement-tabs {
  @apply flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 px-2;
}

.tab-button {
  @apply px-4 py-3 font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors flex items-center;
  position: relative;
}

.tab-button.active {
  @apply text-primary-600 dark:text-primary-400 font-semibold;
}

.tab-button.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background-color: currentColor;
  border-radius: 1px;
}

.announcement-content {
  @apply p-5 overflow-y-auto flex-grow;
  /* 使用固定高度而不是max-height，确保所有标签页高度一致 */
  height: calc(70vh - 130px); /* 减去头部和标签栏的高度 */
  min-height: 350px; /* 确保最小高度 */
}

/* 为标签页内容添加统一的容器 */
.tab-content-container {
  width: 100%;
  height: 100%;
  min-height: 350px;
  display: flex;
  flex-direction: column;
}

/* 标签页切换动画 */
.tab-transition-enter-active,
.tab-transition-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.tab-transition-enter-from,
.tab-transition-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 弹窗淡入淡出动画 */
.announcement-fade-enter-active,
.announcement-fade-leave-active {
  will-change: opacity;
}

.announcement-fade-enter-from,
.announcement-fade-leave-to {
  opacity: 0;
}
</style> 