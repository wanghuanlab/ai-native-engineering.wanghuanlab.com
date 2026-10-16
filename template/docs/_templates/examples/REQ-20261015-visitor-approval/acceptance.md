# 测试与验收报告：REQ-20261015-visitor-approval

## 逐条验收

| 验收标准 | 验证方式 | 证据 | 结果 |
| :--- | :--- | :--- | :--- |
| AC-visitor-appointment-07 | 自动化 | `AppointmentApiIT#ac_visitor_appointment_07_涉密楼层预约进入待审批` | 通过 |
| AC-visitor-appointment-08 | 自动化 | `AppointmentApprovalIT#ac_visitor_appointment_08_审批通过生成通行码` | 通过 |
| AC-visitor-appointment-08 | 人工 | 测试环境用本人手机号预约 12 层并审批通过，收到短信；截图 `raw/ac-08-sms.png` | 通过 |
| AC-visitor-appointment-09 | 自动化 | `AppointmentTest#ac_visitor_appointment_09_驳回必须填写原因` | 通过 |
| AC-visitor-appointment-10 | 自动化 | `AppointmentApprovalIT#ac_visitor_appointment_10_非被访人不能审批` | 通过 |
| AC-visitor-appointment-11 | 自动化 | `VisitorUpgradeIT#ac_visitor_appointment_11_存量预约照常核销`（从 v1.3.0 数据升级后核销） | 通过 |

## 完整校验记录

```text
✓ AI 配置一致性
✓ 迁移脚本
✓ 测试删除检查
✓ 密钥扫描
✓ 后端格式、单元测试与集成测试
✓ 前端检查与构建
✓ 升级路径（v1.2.0, v1.3.0）
执行人：李强  时间：2026-10-17 11:20  提交：3f2a9c1
```

## 已知问题与遗留事项

- 审批超时自动处理未做（范围外，已登记下期需求）。

## 验收结论

> **仅限负责工程师填写**。

| 验收人 | 时间 | 结论 |
| :--- | :--- | :--- |
| 李强 | 2026-10-17 11:30 | 通过 |

## 自审报告

| 检查项 | 结论 |
| :--- | :--- |
| 范围 | 通过 |
| 完整性 | 通过：BR-09～12 均已实现，AC-07～11 均有证据 |
| 数据库 | 通过：两种方言一致，存量数据取默认值 |
| 接口 | 通过：`passCode` 可空已在 design.md 声明 |
| 安全 | 通过：审批接口校验被访人身份 |
| 质量 | 有问题（低）：待办列表查询被访人姓名存在 N+1，已改为批量查询 |
| 测试 | 通过：`ac_visitor_appointment_02` 按设计调整，未删除 |

需要 TL 重点看：`AppointmentService#approve` 的事务边界与异步短信。
