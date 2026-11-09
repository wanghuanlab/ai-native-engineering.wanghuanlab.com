import { currentMenuLoader, type MenuItem } from '@/plugins/host'
import { menusFromChildren } from '@/router/menuItems'
import { routes } from '@/router'

/** 未替换菜单来源时，侧栏使用静态路由。 */
export function staticMenus(): MenuItem[] {
  return menusFromChildren(routes[0]?.children ?? [])
}

/** 当前应展示的菜单。插件通过 setMenuLoader 替换来源。 */
export async function loadMenus(): Promise<MenuItem[]> {
  const custom = currentMenuLoader()
  if (!custom) {
    return staticMenus()
  }
  return custom()
}
