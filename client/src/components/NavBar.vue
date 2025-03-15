<template>
  <nav class="navbar">
    <div class="container">
      <div class="navbar-brand">
        <router-link to="/" class="brand-link">
          <img src="../assets/ai-logo.svg" alt="AI Logo" class="logo" />
          <span class="brand-text">AI</span>
        </router-link>
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
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAnnouncementStore } from '../stores/announcement';
import { useThemeStore } from '../stores/theme';
import { MagnifyingGlassIcon, SunIcon, MoonIcon, MegaphoneIcon } from '@heroicons/vue/24/outline';

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

// 初始化主题
onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark-theme');
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

@media (max-width: 768px) {
  .search-input {
    width: 120px;
  }
  
  .nav-links {
    gap: 1rem;
  }
}

@media (max-width: 576px) {
  .brand-text {
    display: none;
  }
  
  .search-input {
    width: 100px;
  }
  
  .navbar-actions {
    gap: 0.25rem;
  }
}
</style> 