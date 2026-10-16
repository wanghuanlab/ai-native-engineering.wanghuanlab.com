import { setApiErrorHandler } from '@/api'
import ElementPlus, { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

setApiErrorHandler((error) => {
  const traceId = error.problem.traceId ? `（追踪号：${error.problem.traceId}）` : ''
  ElMessage.error(`${error.message}${traceId}`)
})

createApp(App).use(createPinia()).use(router).use(ElementPlus, { locale: zhCn }).mount('#app')
