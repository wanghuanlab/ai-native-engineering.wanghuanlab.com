---
id: 15-quality-gate
title: 质量门禁
scope: glob
globs: backend/**/*.java, backend/**/pom.xml, backend/quality/**
summary: 改后端代码、POM 或质量规则前读取；门禁失败要修代码，不要把检查关掉
---
# 质量门禁

人和 AI 的代码走同一套检查。分层说明在 `docs/standards/java-coding-standard.md`。

- 排版：`cd backend && ./mvnw spotless:apply`（Palantir Java Format）。不要手改缩进和换行。
- 命名和结构：Checkstyle，规则在 `backend/quality/checkstyle.xml`。星号 import、空 catch、`System.out`、`printStackTrace` 会失败。
- 缺陷和可扫描的安全问题：SpotBugs + Find Security Bugs。契约生成的 `web.dto`、`web.api` 已排除。
- 工程实践：`.ai/rules/25-alibaba-java.md`（黄山版）。不要再引入 P3C 的 Maven 插件。
- 安全底线：`.ai/rules/70-security.md`。
- 架构：ArchUnit / Modulith 测试失败就停，不要放宽规则。
- 推送前必须能通过 `./scripts/verify.sh quick`。合并前必须能通过 `./scripts/verify.sh full`（含 JaCoCo，下限是 `backend/quality/coverage-minimum.txt`）。
- 禁止 `-DskipTests`、`checkstyle.skip`、`spotbugs.skip`、`jacoco.skip`、`spotless.skip`，也禁止把 `backend/quality/` 改松来让检查通过。
