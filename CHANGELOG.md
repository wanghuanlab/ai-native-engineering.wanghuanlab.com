# 变更记录

## 未发布

- 基线来源：`new-project` 写入 `.baseline/copier-answers.yml` 的 `_src_path` 改为团队可访问的 Git 地址，并固定标签或提交。默认取基线仓库 `origin`（去掉 URL 中的凭据），可用 `--source` / `BASELINE_SOURCE` 与 `--ref` / `BASELINE_REF` 覆盖。`sync-baseline` 拒绝本机路径，在更新前检查远端能否访问以及引用是否存在；地址变化时先单独提交 answers 文件。
- Windows：开发者命令（setup、verify、new-change、new-module、sync-baseline、db-schema、upgrade-path、release-pack、new-project）的逻辑集中在 Python，`.sh`、`.cmd`、`.ps1` 只负责启动。Git 钩子仍由 Git for Windows 自带的 sh 调用 Python。`.gitattributes` 约定 `.cmd` / `.ps1` 使用 CRLF。服务端 `pre-receive` 与维护者自测 `bin/selftest.sh` 仍是 Bash。
- 门禁：`scripts/verify.sh` 的前端检查在任一命令失败时即失败。此前步骤放在 `if` 中执行，Bash 会忽略 `set -e`，类型检查失败仍可能被后面成功的 lint 记为通过。
- 门禁：密钥扫描按内容跳过二进制文件（含空字节，或无法按 UTF-8 解码）。暂存 `.glb`、`.webp`、`.xlsx`、`.pyc` 等未列入扩展名名单的文件时，不再因 `UnicodeDecodeError` 中断提交钩子；文本文件中的密钥仍会拦截。
- 忽略 Python 的 `__pycache__/`。
- 自测 `bin/selftest.sh` 增加上述反向用例。

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
