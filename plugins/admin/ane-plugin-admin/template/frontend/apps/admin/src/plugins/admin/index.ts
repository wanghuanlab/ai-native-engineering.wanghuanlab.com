import { setHeaderActions, type FrontendPluginContext } from '@/plugins/host'
import type { Router } from 'vue-router'
import { permDirective } from './account'
import { http, logout } from './api'
import { guard, resetSession } from './guard'
import { readAccess, skipsAuthorization } from './session'

/** 登录页不进布局，所以在 install 里注册，而不是放进 routes。 */
export function install(ctx: FrontendPluginContext): void {
  ctx.app.directive('perm', permDirective)
  http.interceptors.request.use((config) => {
    const access = readAccess()
    const url = config.url ?? ''
    if (access && !skipsAuthorization(url, config.method)) {
      config.headers.set('Authorization', `Bearer ${access}`)
    }
    return config
  })
  if (!ctx.router.hasRoute('admin-login')) {
    ctx.router.addRoute({
      path: '/login',
      name: 'admin-login',
      component: () => import('./LoginView.vue'),
      meta: { title: '登录' },
    })
  }
  ctx.router.beforeEach((to) => guard(ctx.router, to))
  setHeaderActions([{ label: '退出', onClick: () => void signOut(ctx.router) }])
}

async function signOut(router: Router): Promise<void> {
  try {
    await logout()
  } catch {
    // 令牌已经失效时，仍然清掉本地会话。
  }
  resetSession(router)
  await router.push({ name: 'admin-login' })
}
