---
name: test-accept
description: 测试与业务验收。实现完成后使用：为每条验收标准编写自动化测试或人工验证步骤，运行完整校验，填写 acceptance.md 作为验收证据。
---
# 测试与验收

## 必读文件

1. `docs/changes/<REQ>/spec-delta.md`（全部 `AC-*`）
2. `.ai/rules/60-testing.md`
3. 涉及模块的已有测试

## 步骤

1. 逐条列出本次的验收标准，为每条选择验证方式：
   - 领域规则 → 单元测试
   - 数据库、接口、权限、存量数据 → 集成测试（`backend/app/src/test/`，Testcontainers）
   - 页面交互、视觉效果 → 人工验证（写出操作步骤，由工程师执行并截图）
2. 编写测试，测试名包含 AC 编号。涉及存量数据的标准，测试中要先构造旧数据，再验证新逻辑。
3. 运行 `./scripts/verify.sh full`。
4. 按 `docs/_templates/acceptance.md` 填写 `acceptance.md`（示范见 `docs/_templates/examples/REQ-20261015-visitor-approval/acceptance.md`）：每条 AC 写明验证方式、证据（测试类与方法名，或人工步骤与截图路径）、结果。
5. 人工验证项交给工程师执行，由工程师填写结果。

## 完成标准

- 每条 AC 都有"通过"的证据。
- `./scripts/verify.sh full` 通过，结果摘要写入 `acceptance.md`。
- 下一步：执行 Skill `self-review`。

## 必须停下来

- 某条 AC 无法验证。
- 已有测试失败，且原因是业务规则变化而 `design.md` 中没有说明。
