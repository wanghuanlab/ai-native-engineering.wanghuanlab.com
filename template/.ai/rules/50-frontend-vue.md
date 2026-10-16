---
id: 50-frontend-vue
title: 前端 Vue 规范
scope: glob
globs: frontend/**/*.vue, frontend/**/*.ts
summary: 修改 frontend/ 下的页面、组件、脚本前读取
---
# 前端 Vue 规范

- 组件一律使用 `<script setup lang="ts">`，不写 `.js` 文件，不用 `any`。
- 接口调用只用生成的函数：`import { listXxx } from '@<项目代号>/api-client/generated/<模块>'`；不要手写 axios 请求和接口类型。
- 契约变化后先运行 `pnpm gen:api`，再根据 `pnpm typecheck` 报错修改页面。
- 错误提示由 `main.ts` 中的 `setApiErrorHandler` 统一处理，页面里不重复弹错误。
- 页面放在 `apps/admin/src/views/<模块>/`，路由在 `src/router/index.ts` 中按模块追加。
- 组件库只用 Element Plus；不引入其他 UI 组件库。
- Pinia 只存全局界面状态和会话信息，服务端数据不放进 store。
- 单个 `.vue` 文件超过 300 行时，拆出子组件或 `use*.ts` 组合函数。
- 格式由 Prettier 统一：运行 `pnpm format`。
