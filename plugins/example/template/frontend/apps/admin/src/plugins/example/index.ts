import type { FrontendPluginContext } from '@/plugins/host'
import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: 'sample/items',
    name: 'sample-items',
    component: () => import('./SampleView.vue'),
    meta: { title: '示例插件' },
  },
]

/** 路由已由基线收集时不再重复注册。 */
export function install(ctx: FrontendPluginContext): void {
  const route = routes[0]
  if (!route || ctx.router.hasRoute('sample-items')) {
    return
  }
  ctx.router.addRoute('layout', route)
}
