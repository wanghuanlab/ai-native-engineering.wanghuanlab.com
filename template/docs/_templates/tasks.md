# 任务清单：__REQ_ID__

> 兼作会话检查点：每次会话开始先读本文件，结束前更新进度和备注。

## 修改范围

- 允许修改：
- 禁止修改：其他模块、基线托管文件（`.baseline/managed-files.txt`）

## 任务

- [ ] T1 新增迁移脚本（每个方言一份）  验证：`./scripts/verify.sh db`
- [ ] T2 更新接口契约并生成前端客户端  验证：`cd frontend && pnpm gen:api && pnpm typecheck`
- [ ] T3 后端实现  验证：`./scripts/verify.sh backend`
- [ ] T4 前端实现  验证：`./scripts/verify.sh frontend`
- [ ] T5 测试与验收  验证：`./scripts/verify.sh full`

## 进度与注意事项

| 时间 | 进度 | 注意事项 |
| :--- | :--- | :--- |
| | | |
