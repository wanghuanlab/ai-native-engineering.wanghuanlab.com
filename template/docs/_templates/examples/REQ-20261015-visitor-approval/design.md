# 技术设计：REQ-20261015-visitor-approval

## 影响分析

| 对象 | 影响 |
| :--- | :--- |
| 表 | `visitor_appointment` 新增 `approval_required`、`approval_status`、`reject_reason`、`approved_by`、`approved_at`；`floor` 新增 `approval_required` |
| 接口 | `POST /api/visitor/appointments` 返回值新增 `approvalStatus`，`passCode` 改为可空；新增 `POST /api/visitor/appointments/{id}/approve`、`/reject` |
| 模块 | `visitor`；通过 `notify` 模块的 `api.SmsFacade` 发短信 |
| 页面 | 管理端"我的待办"新增审批列表；访客端预约详情显示审批状态 |
| 已有测试 | `AppointmentServiceTest#ac_visitor_appointment_02_预约成功生成通行码`：与新规则冲突，改为只覆盖无需审批的楼层，另增需审批楼层的用例 |

## 方案与取舍

| 方案 | 优点 | 缺点 | 结论 |
| :--- | :--- | :--- | :--- |
| A：在预约表上加审批字段 | 改动小，查询简单 | 不支持多级审批 | 采用（多级审批不在范围内） |
| B：独立审批表 + 通用审批流 | 可扩展 | 本期过度设计 | 不采用 |

## 数据库变更与存量兼容

- 迁移脚本（PostgreSQL 与达梦各一份）：
  - `V202610151400__visitor_add_approval.sql`：加字段，`approval_required` 默认 `FALSE`，`approval_status` 可空。
  - `V202610151410__visitor_floor_add_approval.sql`：`floor.approval_required` 默认 `FALSE`，并把 12、13 层设为 `TRUE`。
- 存量数据处理：存量预约的 `approval_required` 取默认值 `FALSE`，满足 BR-visitor-appointment-12，不需要额外的数据迁移。
- 每个在用版本的升级影响：v1.2.0（A 园区）、v1.3.0（B 园区）均为纯加字段，升级路径测试覆盖。
- 多步变更：不涉及删除字段。

## 接口变更与兼容性

- 是否为破坏性修改：是。`passCode` 由必填改为可空，访客端旧版本会把空值当作异常。
- 过渡方式：访客端与后端同版本发布；后端对未升级的访客端（请求头无 `X-Client-Version`）在待审批时返回提示文案。

## 风险与回退

| 风险 | 应对 |
| :--- | :--- |
| 被访人不处理审批，访客到访时无通行码 | 前台可在后台手工放行（已有功能）；审批超时处理列入下期 |
| 短信通道失败 | 发送失败记录日志并重试 3 次，不影响审批结果 |

回退方式：新增字段对旧版本应用无影响，回退应用即可，不需要回退数据库。

## TL 审批

> **仅限 TL 填写**，AI 不得填写或修改本节。

| 审批人 | 时间 | 结论 | 意见 |
| :--- | :--- | :--- | :--- |
| 王欢 | 2026-10-15 16:30 | 修改后通过 | 短信重试改为异步，不要阻塞审批事务 |

## 复核意见

- 2026-10-17 王欢：`reject` 接口缺少原因长度校验的契约声明，已补（李强，10-17 已修复）。
