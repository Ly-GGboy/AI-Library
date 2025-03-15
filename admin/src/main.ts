import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  create,
  NButton,
  NCard,
  NSpace,
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NIcon,
  NBreadcrumb,
  NBreadcrumbItem,
  NAvatar,
  NGrid,
  NGridItem,
  NStatistic,
  NSelect,
  NDatePicker,
  NRadioGroup,
  NRadioButton,
  NDataTable,
  NTag,
  NH2,
  NText
} from 'naive-ui'

import App from './App.vue'
import router from './router'

const naive = create({
  components: [
    NButton,
    NCard,
    NSpace,
    NLayout,
    NLayoutSider,
    NLayoutHeader,
    NLayoutContent,
    NMenu,
    NIcon,
    NBreadcrumb,
    NBreadcrumbItem,
    NAvatar,
    NGrid,
    NGridItem,
    NStatistic,
    NSelect,
    NDatePicker,
    NRadioGroup,
    NRadioButton,
    NDataTable,
    NTag,
    NH2,
    NText
  ]
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')
