import type { MenuItem } from '@/plugins/host'

/** 菜单只读取路径和标题，测试不必构造完整路由记录。 */
interface MenuRoute {
  path: string
  name?: unknown
  meta?: object
}

/** 把路由的 meta.title 转成侧栏菜单。path 为空的子路由表示首页。 */
export function menusFromChildren(children: readonly MenuRoute[]): MenuItem[] {
  return children.map((route) => ({
    path: route.path ? `/${route.path}` : '/',
    title: routeTitle(route),
  }))
}

function routeTitle(route: MenuRoute): string {
  const meta = route.meta
  const titled = meta && 'title' in meta ? meta.title : undefined
  return String(titled ?? route.name ?? route.path)
}
