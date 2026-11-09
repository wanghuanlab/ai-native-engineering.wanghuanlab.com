import { hasPerm, permDirective, setPermissions } from '@/plugins/admin/account'
import { firstMenuPath, menuTree, type NavMenu } from '@/plugins/admin/menus'
import { clearSession, skipsAuthorization, writeSession } from '@/plugins/admin/session'
import { describe, expect, it } from 'vitest'
import { createApp, defineComponent, h, withDirectives } from 'vue'

const system: NavMenu = {
  id: '10',
  name: '系统管理',
  path: 'system',
  menuType: 'DIR',
  visible: true,
  children: [
    {
      id: '11',
      name: '用户管理',
      path: 'users',
      component: 'admin/users',
      permission: 'system:user:list',
      menuType: 'MENU',
      visible: true,
    },
    {
      id: '16',
      name: '新增用户',
      menuType: 'BUTTON',
      visible: true,
      permission: 'system:user:create',
    },
    {
      id: '19',
      name: '隐藏菜单',
      path: 'hidden',
      menuType: 'MENU',
      visible: false,
    },
  ],
}

describe('menuTree', () => {
  it('拼出完整路径，并跳过按钮和隐藏项', () => {
    expect(menuTree([system])).toEqual([
      {
        path: '/system',
        title: '系统管理',
        children: [{ path: '/system/users', title: '用户管理' }],
      },
    ])
    expect(firstMenuPath(system)).toBe('/system/users')
  })
})

describe('v-perm', () => {
  it('没有权限时拿掉节点，有权限时保留', () => {
    setPermissions(['system:user:list'])
    const Root = defineComponent({
      setup() {
        return () =>
          h('div', [
            withDirectives(h('button', { id: 'create' }, '新建'), [
              [permDirective, 'system:user:create'],
            ]),
            withDirectives(h('button', { id: 'list' }, '查询'), [
              [permDirective, 'system:user:list'],
            ]),
          ])
      },
    })
    const host = document.createElement('div')
    const app = createApp(Root)
    app.mount(host)
    expect(host.querySelector('#create')).toBeNull()
    expect(host.querySelector('#list')?.textContent).toBe('查询')
    expect(hasPerm('system:user:list')).toBe(true)
    app.unmount()
    setPermissions([])
  })
})

describe('session', () => {
  it('登录接口不附带访问令牌，其余请求保留本地令牌', () => {
    expect(skipsAuthorization('/api/admin/captcha', 'post')).toBe(true)
    expect(skipsAuthorization('/api/admin/session', 'POST')).toBe(true)
    expect(skipsAuthorization('/api/admin/session/refresh', 'post')).toBe(true)
    expect(skipsAuthorization('/api/admin/session', 'delete')).toBe(false)
    expect(skipsAuthorization('/api/admin/users', 'get')).toBe(false)

    writeSession('access-token', 'refresh-token')
    expect(localStorage.getItem('ane.admin.accessToken')).toBe('access-token')
    clearSession()
    expect(localStorage.getItem('ane.admin.accessToken')).toBeNull()
  })
})
