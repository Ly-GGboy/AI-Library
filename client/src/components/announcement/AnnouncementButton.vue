<template>
  <button 
    class="announcement-button" 
    @click="openAnnouncement"
    @mouseenter="onHover = true"
    @mouseleave="onHover = false"
    aria-label="打开公告板"
    :title="hasNewUpdates ? '有新的更新!' : '公告和反馈'"
  >
    <Transition name="icon-switch" mode="out-in">
      <BellAlertIcon v-if="hasNewUpdates && !onHover" key="bell-alert" class="w-5 h-5 text-primary-500 dark:text-primary-400" />
      <BellIcon v-else key="bell" class="w-5 h-5 text-gray-600 dark:text-gray-400" />
    </Transition>
    <span v-if="hasNewUpdates" class="notification-badge"></span>
  </button>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue'
import { BellIcon, BellAlertIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  hasNewUpdates: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])
const onHover = ref(false)

const openAnnouncement = () => {
  emit('click')
}
</script>

<style scoped>
.announcement-button {
  @apply p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors;
  position: relative;
  z-index: 95;
  transform-origin: center;
  transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.announcement-button:hover {
  transform: scale(1.1);
}

.announcement-button:active {
  transform: scale(0.95);
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #EF4444;
  z-index: 96;
  box-shadow: 0 0 0 2px white;
  animation: pulse 2s infinite;
}

.dark .notification-badge {
  box-shadow: 0 0 0 2px #1f2937;
}

.icon-switch-enter-active,
.icon-switch-leave-active {
  transition: all 0.2s ease;
}

.icon-switch-enter-from,
.icon-switch-leave-to {
  opacity: 0;
  transform: scale(0.8) rotate(-15deg);
}

@keyframes pulse {
  0% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  
  70% {
    transform: scale(1);
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0);
  }
  
  100% {
    transform: scale(0.95);
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}
</style> 