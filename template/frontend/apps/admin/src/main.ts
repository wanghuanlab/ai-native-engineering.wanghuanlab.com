import { setApiErrorHandler } from '@/api'
import type { FrontendPluginContext } from '@/plugins/host'
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

const pluginModules = import.meta.glob('./plugins/*/index.ts', { eager: true }) as Record<
  string,
  { install?: (ctx: FrontendPluginContext) => void }
>

const app = createApp(App).use(createPinia()).use(router).use(ElementPlus, { locale: zhCn })
for (const plugin of Object.values(pluginModules)) {
  plugin.install?.({ app, router })
}
app.mount('#app')
