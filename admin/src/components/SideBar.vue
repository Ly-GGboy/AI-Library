<template>
  <div class="sidebar" :class="{ 'collapsed': isCollapsed }">
    <div class="sidebar-header">
      <div class="logo">
        <span class="logo-icon">📚</span>
        <span class="logo-text" v-if="!isCollapsed">AI Library</span>
      </div>
      <button class="collapse-btn" @click="toggleCollapse">
        <span class="arrow-icon">{{ isCollapsed ? '→' : '←' }}</span>
      </button>
    </div>
    
    <nav class="sidebar-nav">
      <ul class="nav-list">
        <li class="nav-item">
          <router-link to="/" class="nav-link" :class="{ 'active': isActive('/') }">
            <span class="nav-icon">📊</span>
            <span class="nav-text" v-if="!isCollapsed">仪表盘</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="/stats" class="nav-link" :class="{ 'active': isActive('/stats') }">
            <span class="nav-icon">📈</span>
            <span class="nav-text" v-if="!isCollapsed">访问统计</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="/feedback" class="nav-link" :class="{ 'active': isActive('/feedback') }">
            <span class="nav-icon">💬</span>
            <span class="nav-text" v-if="!isCollapsed">用户反馈</span>
          </router-link>
        </li>
      </ul>
    </nav>
    
    <div class="sidebar-footer">
      <a href="https://ailibrary.space" target="_blank" class="back-link">
        <span class="nav-icon">🏠</span>
        <span class="nav-text" v-if="!isCollapsed">返回主站</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isCollapsed = ref(false)

// 检查是否为活动路由
const isActive = (path: string) => {
  return route.path === path
}

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebarCollapsed', isCollapsed.value ? 'true' : 'false')
}

// 初始化折叠状态
const initCollapsedState = () => {
  const savedState = localStorage.getItem('sidebarCollapsed')
  if (savedState) {
    isCollapsed.value = savedState === 'true'
  }
}

// 初始化组件
onMounted(() => {
  initCollapsedState()
})
</script>

<style scoped>
.sidebar {
  width: 250px;
  height: 100vh;
  background-color: #2c3e50;
  color: #ecf0f1;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}

.sidebar.collapsed {
  width: 70px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
  display: flex;
  align-items: center;
  font-weight: 700;
  font-size: 1.25rem;
  white-space: nowrap;
  overflow: hidden;
}

.logo-icon {
  font-size: 1.5rem;
  margin-right: 0.75rem;
}

.logo-text {
  background: linear-gradient(135deg, #3498db, #2ecc71);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}

.collapse-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #ecf0f1;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.arrow-icon {
  font-size: 0.9rem;
}

.sidebar-nav {
  flex: 1;
  padding: 1.5rem 0;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin-bottom: 0.75rem;
}

.nav-link {
  display: flex;
  align-items: center;
  padding: 0.875rem 1.5rem;
  text-decoration: none;
  color: #ecf0f1;
  white-space: nowrap;
  transition: all 0.2s;
  border-left: 3px solid transparent;
  border-radius: 0 4px 4px 0;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateX(3px);
}

.nav-link.active {
  background-color: rgba(52, 152, 219, 0.2);
  border-left: 3px solid #3498db;
  color: #3498db;
}

.nav-icon {
  font-size: 1.25rem;
  width: 24px;
  text-align: center;
  margin-right: 1rem;
  transition: transform 0.2s;
}

.nav-link:hover .nav-icon {
  transform: scale(1.1);
}

.sidebar.collapsed .nav-icon {
  margin-right: 0;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.back-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: #ecf0f1;
  padding: 0.75rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.back-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateX(3px);
}

/* 滚动条样式 */
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  
  .sidebar.collapsed {
    width: 0;
    padding: 0;
    overflow: hidden;
  }
  
  .logo-text,
  .nav-text {
    display: none;
  }
  
  .nav-icon {
    margin-right: 0;
  }
}
</style> 