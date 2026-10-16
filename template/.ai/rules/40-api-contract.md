---
id: 40-api-contract
title: 接口契约规范
scope: glob
globs: contracts/**
summary: 新增或修改接口契约前读取
---
# 接口契约规范

- 每个模块一个契约文件 `contracts/openapi/<模块>.yaml`；公共结构只放在 `common.yaml`，只能新增不能修改。
- 先改契约，再生成代码：后端构建时自动生成接口，前端运行 `cd frontend && pnpm gen:api`。
- 路径：`/api/<模块>/<资源复数>`，例如 `/api/visitor/appointments/{id}`；动作用子路径 `POST .../{id}/approve`。
- 每个操作必须有 `operationId`（小驼峰动宾结构，如 `listVisitorAppointments`）和 `tags`（模块的资源名）。
- 主键引用 `common.yaml#/components/schemas/Id`（字符串）。
- 分页参数引用 `common.yaml` 的 `Page`、`Size`；分页响应结构为 `{ items, total, page, size }`。
- 成功响应直接返回数据，不包信封；错误响应统一为 `ProblemDetail`（带 `code`、`traceId`）。
- 枚举值用大写英文，并在 `description` 中写明含义。
- 已发布的接口只允许兼容扩展：新增可选字段、新增接口。删除、重命名、改类型属于 L 级。
