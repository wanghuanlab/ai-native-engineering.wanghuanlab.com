import { ElMessageBox } from 'element-plus'

/** 用户取消时返回 false，不把取消当成失败。 */
export async function confirmed(message: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, '请确认', { type: 'warning' })
    return true
  } catch {
    return false
  }
}
