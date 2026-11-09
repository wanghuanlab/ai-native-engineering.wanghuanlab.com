import { ref, type App, type Ref } from 'vue'
import type { RouteRecordRaw, Router } from 'vue-router'

/** 侧栏一条菜单。path 以 / 开头。有 children 时渲染成子菜单。 */
export interface MenuItem {
  path: string
  title: string
  children?: MenuItem[]
}

/** 顶栏上的一个操作，例如退出登录。 */
export interface HeaderAction {
  label: string
  onClick: () => void
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

const loader = ref<MenuLoader | null>(null)
const headerActionState = ref<HeaderAction[]>([])

/** 用自定义来源替换静态菜单。传 null 则恢复为静态路由。 */
export function setMenuLoader(next: MenuLoader | null): void {
  loader.value = next
}

/** 当前菜单来源。没有替换时返回 null，调用方使用静态路由。 */
export function currentMenuLoader(): MenuLoader | null {
  return loader.value
}

/** 替换顶栏操作。传空数组则不显示。 */
export function setHeaderActions(actions: readonly HeaderAction[]): void {
  headerActionState.value = [...actions]
}

/** 顶栏操作。布局在模板里读取，注册之后会更新。 */
export function headerActionList(): Ref<HeaderAction[]> {
  return headerActionState
}
