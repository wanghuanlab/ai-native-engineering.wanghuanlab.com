import type { App } from 'vue'
import type { RouteRecordRaw, Router } from 'vue-router'

/** 侧栏一条菜单。path 以 / 开头。 */
export interface MenuItem {
  path: string
  title: string
}

/** 菜单来源。认证插件可换成后端返回的菜单树。 */
export type MenuLoader = () => MenuItem[] | Promise<MenuItem[]>

/** 传给插件 install 的上下文。 */
export interface FrontendPluginContext {
  app: App
  router: Router
}

/** 插件入口 src/plugins/&lt;名称&gt;/index.ts 的导出。 */
export interface FrontendPlugin {
  routes?: RouteRecordRaw[]
  install?: (ctx: FrontendPluginContext) => void
}

let loader: MenuLoader | null = null

/** 用自定义来源替换静态菜单。传 null 则恢复为静态路由。 */
export function setMenuLoader(next: MenuLoader | null): void {
  loader = next
}

/** 当前菜单来源。没有替换时返回 null，调用方使用静态路由。 */
export function currentMenuLoader(): MenuLoader | null {
  return loader
}
