---
id: 60-testing
title: 测试规范
scope: glob
globs: backend/**/src/test/**, frontend/**/tests/**
summary: 编写或修改测试前读取
---
# 测试规范

- 单元测试遵守 AIR：自动、独立、可重复。测试的依据是验收标准：每条 `AC-*` 至少对应一个自动化测试，或在 `acceptance.md` 中有人工验证记录。
- 测试名必须包含 AC 编号，例如 `@DisplayName("[AC-visitor-03] 审批通过后生成通行码")`。
- 分层：
  - 领域规则用单元测试（`*Test.java`，不启动 Spring），放在对应模块。
  - 数据库与接口用集成测试（`*IT.java`，Testcontainers 真实数据库），放在 `backend/app/src/test/`，引入 `PostgresContainerConfig`。
  - 前端组件测试放在 `apps/<应用>/tests/*.spec.ts`。
- 缺陷修复先写一个能稳定复现缺陷的失败测试，再修复。
- 禁止：删除已有测试、`@Disabled`、`.skip`、把断言改弱。确实需要修改已有测试时，在 `design.md` 中说明原因并经 TL 认可。
- 运行：`./scripts/verify.sh backend`（单元）、`./scripts/verify.sh full`（含集成测试）。
