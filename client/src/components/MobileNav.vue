<template>
  <div class="mobile-nav">
    <button 
      class="nav-toggle"
      @click="$emit('toggle')"
      aria-label="Toggle navigation"
    >
      <Bars3Icon v-if="isHidden" class="w-6 h-6" />
      <XMarkIcon v-else class="w-6 h-6" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'

defineProps<{
  isHidden: boolean
}>()

defineEmits<{
  (e: 'toggle'): void
}>()
</script>

<style scoped>
.mobile-nav {
  @apply fixed top-4 left-4 z-50;
}

.nav-toggle {
  @apply p-2 rounded-full bg-white/80 shadow-lg
    dark:bg-gray-800/80 backdrop-blur-sm
    text-gray-600 dark:text-gray-300
    hover:bg-gray-100 dark:hover:bg-gray-700
    transition-all duration-200;
}
</style> 