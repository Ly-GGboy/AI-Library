<template>
  <nav class="navbar">
    <div class="container">
      <div class="navbar-brand">
        <router-link to="/" class="brand-link">
          <img src="../assets/ai-logo.svg" alt="AI Logo" class="logo" />
          <span class="brand-text">AI</span>
        </router-link>
        
        <!-- 在线阅读人数显示 - 移动到左侧 -->
        <div class="online-readers" v-if="onlineReadersCount !== null">
          <UserGroupIcon class="icon" />
          <span class="count">{{ onlineReadersCount }}</span>
          <span class="label">在线</span>
        </div>
        
        <!-- GitHub图标 -->
        <a href="https://github.com" target="_blank" class="github-link">
          <GithubIcon class="icon" />
        </a>
      </div>
      
      <div class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="active">首页</router-link>
        <router-link to="/docs" class="nav-link" active-class="active">文档</router-link>
        <router-link to="/admin" class="nav-link" active-class="active">管理后台</router-link>
      </div>
      
      <div class="navbar-actions">
        <div class="search-box">
          <input 
            type="text" 
            placeholder="搜索..." 
            class="search-input" 
            v-model="searchQuery"
            @keyup.enter="handleSearch"
          />
          <button class="search-button" @click="handleSearch">
            <MagnifyingGlassIcon class="icon" />
          </button>
        </div>
        
        <button class="theme-toggle" @click="toggleTheme">
          <SunIcon v-if="themeStore.isDark" class="icon" />
          <MoonIcon v-else class="icon" />
        </button>
        
        <button class="announcement-button" @click="openAnnouncement">
          <MegaphoneIcon class="icon" />
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAnnouncementStore } from '../stores/announcement';
import { useThemeStore } from '../stores/theme';
import { MagnifyingGlassIcon, SunIcon, MoonIcon, MegaphoneIcon, UserGroupIcon } from '@heroicons/vue/24/outline';
import { GithubIcon } from './icons';
import { docApi } from '../services/api';

const router = useRouter();
const announcementStore = useAnnouncementStore();
const themeStore = useThemeStore();

// 搜索功能
const searchQuery = ref('');

const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      path: '/search',
      query: { q: searchQuery.value }
    });
    searchQuery.value = '';
  }
};

// 主题切换
const isDarkMode = ref(false);

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value;
  document.documentElement.classList.toggle('dark-theme', isDarkMode.value);
  localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
};

// 打开公告板
const openAnnouncement = () => {
  announcementStore.toggleVisibility(true);
};

// 在线阅读人数
const onlineReadersCount = ref(null);
let onlineReadersTimer = null;

const fetchOnlineReadersCount = async () => {
  try {
    const response = await docApi.getOnlineReadersCount();
    onlineReadersCount.value = response.count;
  } catch (error) {
    console.error('获取在线阅读人数失败:', error);
  }
};

// 初始化
onMounted(() => {
  // 初始化主题
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark-theme');
  }
  
  // 立即获取一次在线阅读人数，然后设置定时刷新
  fetchOnlineReadersCount();
  onlineReadersTimer = setInterval(fetchOnlineReadersCount, 60000); // 每分钟更新一次
});

// 组件卸载时清除定时器
onUnmounted(() => {
  if (onlineReadersTimer) {
    clearInterval(onlineReadersTimer);
  }
});
</script>

<style scoped>
.navbar {
  background-color: var(--color-bg-primary);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
  padding: 0.75rem 0;
}

.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: var(--color-text-primary);
  font-weight: 600;
}

.logo {
  height: 32px;
  margin-right: 0.5rem;
}

.brand-text {
  font-size: 1.25rem;
}

.github-link {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.github-link:hover {
  color: var(--color-text-primary);
  background-color: var(--color-bg-secondary);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  text-decoration: none;
  color: var(--color-text-secondary);
  font-weight: 500;
  padding: 0.5rem 0;
  position: relative;
}

.nav-link:hover {
  color: var(--color-text-primary);
}

.nav-link.active {
  color: var(--color-primary);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: var(--color-primary);
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-box {
  display: flex;
  align-items: center;
  background-color: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 0.25rem 0.5rem;
}

.search-input {
  background: transparent;
  border: none;
  padding: 0.5rem;
  color: var(--color-text-primary);
  outline: none;
  width: 200px;
}

.dark .search-input {
  color: var(--dark-text-primary);
  background: transparent;
}

.search-input::placeholder {
  color: var(--color-text-secondary);
}

.dark .search-input::placeholder {
  color: var(--dark-text-secondary);
}

.search-button {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
}

.theme-toggle, .announcement-button {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  width: 36px;
  height: 36px;
  border-radius: 8px;
}

.theme-toggle:hover, .announcement-button:hover, .search-button:hover {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.icon {
  width: 20px;
  height: 20px;
}

.online-readers {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background-color: var(--color-bg-secondary);
  border-radius: 8px;
  padding: 0.25rem 0.5rem;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.online-readers:hover {
  background-color: rgba(var(--primary-color), 0.1);
}

.online-readers .icon {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
}

.online-readers .count {
  font-weight: 600;
  color: var(--color-primary);
}

.online-readers .label {
  color: var(--color-text-secondary);
}

@media (max-width: 768px) {
  .search-input {
    width: 120px;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .online-readers .label {
    display: none;
  }
  
  .github-link {
    margin-left: -0.25rem;
  }
}

@media (max-width: 576px) {
  .brand-text {
    display: none;
  }
  
  .search-input {
    width: 100px;
  }
  
  .navbar-brand {
    gap: 0.5rem;
  }
}
</style> 