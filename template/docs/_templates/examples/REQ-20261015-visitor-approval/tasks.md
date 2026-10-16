# 任务清单：REQ-20261015-visitor-approval

## 修改范围

- 允许修改：`backend/modules/visitor/**`，`contracts/openapi/visitor.yaml`，`db/migration/*/V2026101514*__visitor_*.sql`，`frontend/apps/admin/src/views/visitor/**`，`docs/specs/visitor-appointment/`（归档时）
- 禁止修改：其他模块（`notify` 只通过 `api` 包调用）、基线托管文件

## 任务

- [x] T1 新增迁移脚本（PostgreSQL / 达梦各两份）  验证：`./scripts/verify.sh db`
      备注：达梦的 BOOLEAN 用 BIT
- [x] T2 更新接口契约并生成前端客户端  验证：`cd frontend && pnpm gen:api && pnpm typecheck`
- [x] T3 后端实现审批流转（BR-09～12）  验证：`./scripts/verify.sh backend`
      备注：存量预约 approval_required=false，不得拦截其核销
- [x] T4 短信改为异步发送（TL 审批意见）  验证：`./scripts/verify.sh backend`
- [x] T5 管理端审批列表  验证：`./scripts/verify.sh frontend`
- [x] T6 测试与验收  验证：`./scripts/verify.sh full`

## 进度与注意事项

| 时间 | 进度 | 注意事项 |
| :--- | :--- | :--- |
| 10-16 18:00 | T1～T3 完成 | 下次从 T4 开始；`AppointmentServiceTest` 已按设计调整 |
| 10-17 11:00 | 全部完成 | 复核意见已处理 |
