import { setMenuLoader } from '@/plugins/host'
import type { RouteLocationNormalized, RouteLocationRaw, Router } from 'vue-router'
import { setPermissions } from './account'
import { currentAccount, type MenuNode } from './api'
import { menuTree, type NavMenu } from './menus'
import { clearRegisteredRoutes, registerRoutes } from './routes'
import { clearSession, readAccess } from './session'

let ready = false
let loading: Promise<void> | null = null

export function resetSession(router: Router): void {
  ready = false
  loading = null
  clearSession()
  setPermissions([])
  setMenuLoader(null)
  clearRegisteredRoutes(router)
}

/** 没有令牌去登录页；第一次进入时拉取账号、菜单和动态路由。 */
export async function guard(
  router: Router,
  to: RouteLocationNormalized,
): Promise<true | RouteLocationRaw> {
  // 路由是在应用挂载前动态加上的，第一次进入时 name 可能还没对上。
  if (to.name === 'admin-login' || to.path === '/login') {
    return true
  }
  if (!readAccess()) {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  const wasReady = ready
  try {
    await ensureSession(router)
  } catch {
    resetSession(router)
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  if (!wasReady) {
    return to.fullPath
  }
  return true
}

function ensureSession(router: Router): Promise<void> {
  if (ready) {
    return Promise.resolve()
  }
  loading ??= loadSession(router).finally(() => {
    loading = null
  })
  return loading
}

async function loadSession(router: Router): Promise<void> {
  const account = await currentAccount()
  const menus = account.menus.map(toNav)
  setPermissions(account.permissions)
  setMenuLoader(() => [{ path: '/', title: '首页' }, ...menuTree(menus)])
  registerRoutes(router, menus)
  ready = true
}

function toNav(node: MenuNode): NavMenu {
  return {
    id: node.id,
    name: node.name,
    path: node.path,
    component: node.component,
    permission: node.permission,
    menuType: node.menuType,
    visible: node.visible,
    children: node.children?.map(toNav),
  }
}
