<template>
  <n-layout has-sider>
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      :native-scrollbar="false"
      class="admin-sider"
    >
      <!-- Logo -->
      <div class="logo-container">
        <n-icon size="28" class="logo-icon">
          <BookOpen20Regular />
        </n-icon>
        <h1 class="logo-text" v-show="!collapsed">AI Library</h1>
      </div>

      <!-- 导航菜单 -->
      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuUpdate"
      />
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout>
      <!-- 顶部栏 -->
      <n-layout-header bordered class="admin-header">
        <div class="header-left">
          <n-button
            quaternary
            circle
            @click="collapsed = !collapsed"
          >
            <template #icon>
              <n-icon size="20">
                <Navigation20Regular />
              </n-icon>
            </template>
          </n-button>
          <n-breadcrumb>
            <n-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </n-breadcrumb-item>
          </n-breadcrumb>
        </div>
        <div class="header-right">
          <n-space align="center" :size="12">
            <n-button quaternary circle>
              <template #icon>
                <n-icon><AlertOn20Regular /></n-icon>
              </template>
            </n-button>
            <n-button quaternary circle>
              <template #icon>
                <n-icon><Settings20Regular /></n-icon>
              </template>
            </n-button>
            <n-avatar
              round
              size="small"
              src="https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg"
            />
          </n-space>
        </div>
      </n-layout-header>

      <!-- 内容区 -->
      <n-layout-content class="admin-content">
        <router-view></router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  BookOpen20Regular,
  Navigation20Regular,
  ChartMultiple20Regular,
  Person20Regular,
  ChatHelp20Regular,
  AlertOn20Regular,
  Settings20Regular,
  Home20Regular
} from '@vicons/fluent'
import { h } from 'vue'

const router = useRouter()
const route = useRoute()

// 侧边栏折叠状态
const collapsed = ref(false)

// 菜单配置
const menuOptions = [
  {
    label: '仪表盘',
    key: 'dashboard',
    icon: renderIcon(Home20Regular),
    path: '/admin'
  },
  {
    label: '访问统计',
    key: 'stats',
    icon: renderIcon(ChartMultiple20Regular),
    path: '/admin/stats'
  },
  {
    label: '用户反馈',
    key: 'feedback',
    icon: renderIcon(ChatHelp20Regular),
    path: '/admin/feedback'
  }
]

// 渲染图标
function renderIcon(icon: any) {
  return () => h(
    'n-icon',
    { size: 20 },
    { default: () => h(icon) }
  )
}

// 当前激活的菜单项
const activeKey = computed(() => {
  const path = route.path
  const menu = menuOptions.find(item => item.path === path)
  return menu ? menu.key : null
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const currentMenu = menuOptions.find(item => item.path === route.path)
  return [
    { title: '管理后台', path: '/admin' },
    ...(currentMenu ? [{ title: currentMenu.label, path: currentMenu.path }] : [])
  ]
})

// 处理菜单点击
const handleMenuUpdate = (key: string) => {
  const menu = menuOptions.find(item => item.key === key)
  if (menu) {
    router.push(menu.path)
  }
}
</script>

<style scoped>
.admin-sider {
  height: 100vh;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  z-index: 999;
}

.logo-container {
  height: 64px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
}

.logo-icon {
  flex-shrink: 0;
  color: var(--primary-color);
}

.logo-text {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color-base);
  white-space: nowrap;
}

.admin-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-content {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 64px);
}

:deep(.n-menu .n-menu-item) {
  height: 50px;
}

:deep(.n-layout-header) {
  backdrop-filter: blur(8px);
  background: rgba(255, 255, 255, 0.8);
}

:deep(.n-breadcrumb) {
  font-size: 14px;
}
</style> 