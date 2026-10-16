# 部署手册：<版本>

> 面向运维 / 实施。全新部署使用本手册；已有环境升级见 `upgrade-guide.md`。

## 环境要求

| 项 | 要求 |
| :--- | :--- |
| 操作系统与架构 | （x86_64 / ARM64；信创环境写明具体系统） |
| 数据库 | PostgreSQL 17 / 达梦 8 / 人大金仓 V9 |
| 运行环境 | （Docker 或 JDK 21 + Nginx） |
| 端口 | 后端 8080；前端 80 |

## 交付包内容

| 目录 | 内容 |
| :--- | :--- |
| `images/` | 镜像离线包 |
| `app/` | 后端 jar、前端静态文件 |
| `db/<方言>/` | 迁移脚本 |
| `config/` | 配置模板 |

## 部署步骤

1. 导入镜像或解压应用。
2. 按 `config/` 中的模板填写配置（数据库连接、`APP_WORKER_ID` 等）。
3. 执行数据库迁移（独立步骤，执行前备份）：`java -jar app/<项目>-app.jar --spring.profiles.active=migrate,<方言>`
4. 启动后端（`--spring.profiles.active=prod,<方言>`）和前端。
5. 验证：访问 `/actuator/health` 返回 `UP`；登录系统检查首页。

## 部署回执

部署完成后把以下信息发给项目工程师或 TL，登记到 `docs/releases/deployments.md`：客户现场、版本、时间、结果、遇到的问题。
