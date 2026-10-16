# 变更记录

## v0.1.0（2026-10-15，试点版）

首个版本，用于第 1 阶段试点项目。

- 流程：S / M / L 分级、变更包、产物模板 10 份、示范变更包 `REQ-20261015-visitor-approval`。
- AI 协作：规则 10 条（含信创、大屏两条画像规则）、Skills 8 个，规则编译脚本 `build-ai-config.py`。
- 骨架：后端 common 与示例模块、前端管理端与接口客户端、可选大屏应用；PostgreSQL 与达梦 / 金仓迁移脚本。
- 门禁：提交、推送钩子，`verify.sh`，服务端 `pre-receive` 钩子。
- 脚手架：`new-change.sh`、`new-module.sh`、`db-schema.sh`、`upgrade-path.sh`、`release-pack.sh`、`sync-baseline.sh`。

已知限制：

- 达梦、金仓的 JDBC 驱动版本和方言配置待第 0 阶段在真实数据库上验证；自测只覆盖 PostgreSQL。
- Cesium 大屏只有规则，骨架中只提供 Three.js 示例。
- 契约兼容性对比（破坏性变更检测）尚未实现，暂由 TL 复核时人工检查。
