const ACCESS = 'ane.admin.accessToken'
const REFRESH = 'ane.admin.refreshToken'

/** 登录和刷新本身不携带访问令牌，避免过期令牌把公开接口挡在外面。 */
export function skipsAuthorization(url: string, method: string | undefined): boolean {
  const path = url.split('?')[0] ?? ''
  if ((method ?? 'GET').toUpperCase() !== 'POST') {
    return false
  }
  return (
    path.endsWith('/api/admin/captcha') ||
    path.endsWith('/api/admin/session') ||
    path.endsWith('/api/admin/session/refresh')
  )
}

export function readAccess(): string {
  return localStorage.getItem(ACCESS) ?? ''
}

export function writeSession(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS, accessToken)
  localStorage.setItem(REFRESH, refreshToken)
}

export function clearSession(): void {
  localStorage.removeItem(ACCESS)
  localStorage.removeItem(REFRESH)
}
