---
id: 20-backend-java
title: 后端 Java 规范
scope: glob
globs: backend/**/*.java, backend/**/pom.xml
summary: 修改 backend/ 下的 Java 代码或 POM 前读取
---
# 后端 Java 规范

编码强制项同时遵守 `.ai/rules/25-alibaba-java.md`（《Java 开发手册》黄山版）和 `.ai/rules/15-quality-gate.md`。与本文件冲突时，以本文件的分层、事务、MapStruct 和错误码写法为准。

## 模块与分层

- 新模块必须用 `./scripts/new-module.sh <模块名>` 创建，不要手工搭目录。
- 模块包结构：`api`（对其他模块开放的接口和 DTO）、`web`（Controller）、`service`（业务编排与事务）、`domain`（实体、仓储、领域规则）、`infra`（外部系统适配、复杂查询）。
- 其他模块只能依赖本模块的 `api` 包和公共模块 `common`。违反时 `ModularityTest` 失败。
- Controller 只做参数转换和调用 service：不写业务分支、不注入 Repository、不加 `@Transactional`。违反时 `ArchitectureRulesTest` 失败。
- 事务只放在 service 层；查询方法用 `@Transactional(readOnly = true)`。

## 接口实现

- Controller 必须实现由契约生成的接口（`<模块>.web.api.*Api`），DTO 用生成的 `*Dto` 类。先改契约，再写实现。
- 不在 Controller 上另写 `@Operation`、`@Tag`、`@Schema`。这些注解由生成器按契约写出，Knife4j 只负责展示，见 `.ai/rules/45-knife4j.md`。
- 实体与 DTO 的转换用 MapStruct（`web/*WebMapper`），禁止 `BeanUtils.copyProperties`。
- 主键在接口里是字符串：路径参数用 `Ids.parse(id)` 转换。

## JPA

- 实体继承 `BaseEntity`，逻辑删除用 `@SoftDelete(columnName = "deleted")`。
- 关联默认 `FetchType.LAZY`；不跨模块建立实体关联，跨模块只保存对方 ID。
- 不用级联删除；列表查询要说明如何避免 N+1（`@EntityGraph` 或专用查询）。
- 原生 SQL 只能放在 `infra` 包，并且所有启用的数据库方言都要能执行。
- 永远不要把 `ddl-auto` 改成 `update`。

## 错误处理

- 可预期的业务失败抛 `BizException(错误码)`；每个模块定义自己的 `*ErrorCode` 枚举，号段登记在 `docs/context/architecture.md`。
- 不捕获异常后吞掉；不向客户端返回堆栈。

## 写法

- 构造器注入，禁止字段注入。
- 用日志框架输出，禁止 `System.out`。
- 格式由 Spotless 统一：提交前运行 `cd backend && ./mvnw spotless:apply`。
