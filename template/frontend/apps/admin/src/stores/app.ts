import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 全局界面状态。服务端数据不放进 store，由页面通过接口函数获取。 */
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)

  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  return { sidebarCollapsed, toggleSidebar }
})
