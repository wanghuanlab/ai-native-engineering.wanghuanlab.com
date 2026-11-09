<template>
  <template v-for="item in items" :key="item.path">
    <el-sub-menu v-if="item.children?.length" :index="item.path">
      <template #title>{{ item.title }}</template>
      <MenuBranch :items="item.children ?? []" />
    </el-sub-menu>
    <el-menu-item v-else :index="item.path">{{ item.title }}</el-menu-item>
  </template>
</template>

<script setup lang="ts">
import type { MenuItem } from '@/plugins/host'

defineOptions({ name: 'MenuBranch' })

defineProps<{ items: MenuItem[] }>()
</script>
