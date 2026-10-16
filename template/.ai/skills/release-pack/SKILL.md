---
name: release-pack
description: 发布打包。技术负责人准备发布新版本时使用：汇总本版本的变更、迁移脚本和配置项，起草发布说明、部署手册和升级手册，并生成交付包。
---
# 发布打包

只有技术负责人可以发起。AI 起草文档，TL 审阅后打标签、生成交付包。

## 必读文件

1. 上一个版本标签以来的提交：`git log <上一版本>..HEAD --format='%h %s%n%b'`
2. 本版本涉及的变更包：`docs/changes/<REQ>/proposal.md`、`spec-delta.md`
3. 新增的迁移脚本：`git diff --name-only <上一版本>..HEAD -- db/migration`
4. 配置变化：`git diff <上一版本>..HEAD -- backend/app/src/main/resources`
5. 客户版本台账：`docs/releases/deployments.md`
6. 模板：`docs/_templates/release-notes.md`、`deploy-guide.md`、`upgrade-guide.md`

## 步骤

1. 按 `Refs:` 汇总需求和缺陷编号，起草 `docs/releases/<版本>/release-notes.md`。描述用业务语言，面向运维和客户。
2. 列出每个迁移脚本的作用、是否需要停机、是否兼容旧版本应用。
3. 列出配置项的新增、修改、删除，写明默认值和是否必填。
4. 起草 `deploy-guide.md` 和 `upgrade-guide.md`。升级手册覆盖台账「在用版本」中的每个起点。
5. 运行 `./scripts/verify.sh full`（含升级路径测试），把结果写进升级手册的"升级路径测试"列。
6. 交给 TL 审阅。TL 提交文档、打标签后执行 `./scripts/release-pack.sh <版本> [--images]`。

## 不要做

- 不要自己打标签、不要推送 main。
- 不要编造未经验证的停机时间和兼容性结论，不确定时写"待确认"并在输出中提示。

## 完成标准

- 三份文档齐全，每个需求和缺陷编号都出现在发布说明中。
- 交付包 `dist/<项目>-<版本>.tar.gz` 已生成，`checksums.txt` 完整。
- 运维部署后，回执登记到 `docs/releases/deployments.md`，并更新「在用版本」。
