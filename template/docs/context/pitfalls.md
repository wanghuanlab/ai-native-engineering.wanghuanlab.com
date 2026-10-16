# 踩坑记录

> 每次排查出非显而易见的问题后补一条。AI 编码前必读本文件。对其他项目也有价值的条目，整理成基线改进提案。

| 日期 | 现象 | 原因 | 正确做法 |
| :--- | :--- | :--- | :--- |
| 基线自带 | 前端拿到的主键末尾几位变成 0 | 雪花 ID 超出 JavaScript 安全整数范围 | 契约中主键一律用 `Id`（字符串），不要声明为 integer |
| 基线自带 | 启动报 `Schema-validation: missing column` | 实体字段与表结构不一致（`ddl-auto=validate`） | 新增字段先写迁移脚本，再改实体 |
| 基线自带 | 生产环境启动时没有执行迁移 | prod 配置关闭了 Flyway | 生产迁移是独立步骤：`--spring.profiles.active=migrate` |
