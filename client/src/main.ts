import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import '@fortawesome/fontawesome-free/css/all.css'

// 初始化主题
const theme = localStorage.getItem('theme')
if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark')
  localStorage.setItem('theme', 'dark')
} else {
  document.documentElement.classList.remove('dark')
  localStorage.setItem('theme', 'light')
}

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
