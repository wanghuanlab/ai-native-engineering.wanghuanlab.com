import type { MenuItem } from '@/plugins/host'

/** 后端菜单里拼侧栏所需的字段。按钮不是菜单。 */
export interface NavMenu {
  id: string
  name: string
  path?: string
  component?: string
  permission?: string
  menuType: string
  visible: boolean
  children?: NavMenu[]
}

/** 父路径加相对路径，得到以 / 开头的完整路径。 */
export function joinPath(parent: string, path: string | undefined): string {
  if (!path) {
    return parent || '/'
  }
  if (path.startsWith('/')) {
    return path
  }
  const base = parent.endsWith('/') ? parent.slice(0, -1) : parent
  const joined = `${base}/${path}`
  return joined.startsWith('/') ? joined : `/${joined}`
}

/** 目录和菜单组成侧栏树。隐藏项和按钮不出现。 */
export function menuTree(nodes: readonly NavMenu[], parent = ''): MenuItem[] {
  const items: MenuItem[] = []
  for (const node of nodes) {
    if (node.menuType === 'BUTTON' || node.visible === false) {
      continue
    }
    const path = joinPath(parent, node.path)
    const children = menuTree(node.children ?? [], path)
    if (node.menuType === 'DIR' && children.length === 0) {
      continue
    }
    items.push(
      children.length > 0 ? { path, title: node.name, children } : { path, title: node.name },
    )
  }
  return items
}

/** 目录被直接打开时，转到它下面第一个菜单。 */
export function firstMenuPath(node: NavMenu, parent = ''): string | undefined {
  const path = joinPath(parent, node.path)
  if (node.menuType === 'MENU' && node.visible !== false) {
    return path
  }
  for (const child of node.children ?? []) {
    const found = firstMenuPath(child, path)
    if (found) {
      return found
    }
  }
  return undefined
}
