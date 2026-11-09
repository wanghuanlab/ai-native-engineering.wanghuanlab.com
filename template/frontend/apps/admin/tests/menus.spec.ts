import { currentMenuLoader, setMenuLoader } from '@/plugins/host'
import { menusFromChildren } from '@/router/menuItems'
import { describe, expect, it } from 'vitest'

describe('menusFromChildren', () => {
  it('用路由标题生成菜单，空路径表示首页', () => {
    const menus = menusFromChildren([
      { path: '', meta: { title: '首页' } },
      { path: 'example/notes', meta: { title: '示例笔记' } },
    ])

    expect(menus).toEqual([
      { path: '/', title: '首页' },
      { path: '/example/notes', title: '示例笔记' },
    ])
  })
})

describe('setMenuLoader', () => {
  it('可以替换并恢复菜单来源', async () => {
    setMenuLoader(() => [{ path: '/custom', title: '自定义' }])
    const loader = currentMenuLoader()
    expect(await loader?.()).toEqual([{ path: '/custom', title: '自定义' }])

    setMenuLoader(null)
    expect(currentMenuLoader()).toBeNull()
  })
})
