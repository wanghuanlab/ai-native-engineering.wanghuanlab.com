import type { Router } from 'vue-router'
import { firstMenuPath, joinPath, type NavMenu } from './menus'

const views = {
  'admin/users': () => import('./views/UsersView.vue'),
  'admin/roles': () => import('./views/RolesView.vue'),
  'admin/menus': () => import('./views/MenusView.vue'),
  'admin/depts': () => import('./views/DeptsView.vue'),
  'admin/posts': () => import('./views/PostsView.vue'),
} as const

const registered = new Set<string>()

/** 按菜单的 component 挂上页面。目录本身转到第一个子菜单。 */
export function registerRoutes(router: Router, nodes: readonly NavMenu[], parent = ''): void {
  for (const node of nodes) {
    if (node.menuType === 'BUTTON' || node.visible === false) {
      continue
    }
    const full = joinPath(parent, node.path)
    const name = `admin-menu-${node.id}`
    if (!router.hasRoute(name)) {
      if (node.menuType === 'MENU') {
        const load = node.component ? views[node.component as keyof typeof views] : undefined
        if (load) {
          router.addRoute('layout', {
            path: full.replace(/^\//, ''),
            name,
            component: load,
            meta: { title: node.name, permission: node.permission },
          })
          registered.add(name)
        }
      } else if (node.menuType === 'DIR') {
        const target = firstMenuPath(node, parent)
        if (target) {
          router.addRoute('layout', {
            path: full.replace(/^\//, ''),
            name,
            redirect: target,
          })
          registered.add(name)
        }
      }
    }
    if (node.children?.length) {
      registerRoutes(router, node.children, full)
    }
  }
}

export function clearRegisteredRoutes(router: Router): void {
  for (const name of registered) {
    if (router.hasRoute(name)) {
      router.removeRoute(name)
    }
  }
  registered.clear()
}
