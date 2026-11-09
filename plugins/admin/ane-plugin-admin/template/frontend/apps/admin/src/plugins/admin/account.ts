import { ref, type Directive } from 'vue'

const permissions = ref<string[]>([])

export function setPermissions(next: readonly string[]): void {
  permissions.value = [...next]
}

/** 当前账号是否拥有这个权限码。 */
export function hasPerm(code: string): boolean {
  return permissions.value.includes(code)
}

function hideWithoutPerm(el: HTMLElement, code: unknown): void {
  if (typeof code === 'string' && hasPerm(code)) {
    return
  }
  el.parentNode?.removeChild(el)
}

/** v-perm="'system:user:create'"：没有该权限时从页面上拿掉。 */
export const permDirective: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    hideWithoutPerm(el, binding.value)
  },
}
