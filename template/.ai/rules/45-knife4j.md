---
id: 45-knife4j
title: Knife4j 接口文档
scope: glob
globs: backend/**/*.yml, backend/**/*.yaml, contracts/openapi/**
summary: 调整接口文档、Knife4j 或 springdoc 配置前读取；创建项目不访问外网文档
---
# Knife4j 接口文档

骨架已经集成完毕。`bin/new-project.sh` 只复制模板，不访问 Knife4j 网站，也不下载文档。

## 和官方快速开始的关系

官方快速开始（<https://doc.xiaominfo.com/docs/quick-start>，页面标注 2023-12-10 更新）写的是 Spring Boot 3：

- 坐标 `com.github.xiaoymin:knife4j-openapi3-jakarta-spring-boot-starter:4.4.0`（中央仓库最高发行版 4.5.0）
- JDK 17 以上；starter 已经带上 springdoc，不要再引一份
- 配置 `springdoc.swagger-ui`、`springdoc.api-docs`、`springdoc.group-configs` 和 `knife4j.enable`、`knife4j.setting.language`
- 用 OpenAPI 3 注解（`io.swagger.v3.oas.annotations` 的 `@Tag`、`@Operation`、`@Parameter`、`@Schema`）描述接口
- 浏览器打开 `http://<host>:<port>/doc.html`

该坐标传递的 springdoc 2.x 不能在 Spring Boot 4 上运行。本基线是 Spring Boot 4.1，因此使用同一套配置、面向 Boot 4 的发行版：

| 项 | 本基线 |
| :--- | :--- |
| 坐标 | `com.baizhukui:knife4j-openapi3-boot4-spring-boot-starter` |
| 版本属性 | 父 POM 的 `knife4j.version`（当前 5.7.9） |
| 传递的 springdoc | 3.0.3，由 starter 管理，禁止再声明 `springdoc-openapi-*` 或 Springfox |
| 注解库 | `io.swagger.core.v3:swagger-annotations-jakarta`（父 POM 的 `swagger-annotations.version`，当前 2.2.55） |

版本由骨架锁定。升级走基线，不在项目里改版本号。

## 文档从哪来

`contracts/openapi/` 仍是唯一事实源。父 POM 里 openapi-generator 的 `annotationLibrary` 为 `swagger2`，编译时把契约里的摘要、参数、响应写到生成接口的 `@Tag`、`@Operation`、`@Schema` 上。Knife4j 只读取这些生成注解。

- 要改文档内容，改契约后重新编译，不要在 Controller 上再写一套注解。
- 不要改 `target/generated-sources/`。
- 不要把官方示例里的 `BodyController` 抄进业务模块。
- `new-module.sh` 创建的模块 POM 已依赖 `swagger-annotations-jakarta`，生成代码才能编译。

## 已写入骨架的配置

依赖在 `backend/app/pom.xml`。本地与默认配置在 `application.yml`：

- `springdoc.swagger-ui.path=/swagger-ui.html`，标签和操作按字母排序
- `springdoc.api-docs.path=/v3/api-docs`
- `springdoc.group-configs`：分组 `default`，只扫描本项目包，只匹配 `/api/**`
- `knife4j.enable=true`，`knife4j.setting.language=zh_cn`
- 文档标题在 `OpenApiConfig`，接口清单不写在这个类里

本地访问：

- 页面：`http://localhost:8080/doc.html`
- OpenAPI JSON：`http://localhost:8080/v3/api-docs`（若分组路径不同，以 `/v3/api-docs/swagger-config` 列出的地址为准）

## 关闭文档

- 生产配置 `application-prod.yml`：`knife4j.enable=false`、`knife4j.production=true`，并关闭 springdoc 的 api-docs 与 swagger-ui。
- 只跑迁移的 `application-migrate.yml` 同样关闭（该进程 `web-application-type=none`，本来不应起文档）。
- 对外 nginx 只代理 `/api/`。不要增加 `/doc.html`、`/v3/api-docs`、`/swagger-ui.html`、`/swagger-ui/**`、`/webjars/**` 的反向代理。

页面打不开时，先看 starter 是否在 app 模块、`knife4j.enable` 是否为 true、端口和 context-path 是否就是 `http://localhost:8080/doc.html`。页面是空的，先确认对应模块已经用当前契约编译过，生成的 `*Api` 上有 `@Operation`。
