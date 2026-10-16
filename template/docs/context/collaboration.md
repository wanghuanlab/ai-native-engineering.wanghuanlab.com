# 协作流程（裸 Git，无 PR）

## 分支

| 分支 | 用途 | 规则 |
| :--- | :--- | :--- |
| `main` | 主干，随时可发布 | 只有技术负责人（TL）能合并和推送 |
| `feat/<需求编号>`、`fix/<缺陷编号>` | 功能与修复分支 | 尽量不超过一周；大需求拆成多个变更包 |
| `release/<主>.<次>` | 已交付客户的版本线 | 只接收紧急修复，修复后必须合回 main |

不为单个客户建长期分支，客户差异用配置和功能开关实现。

## 一个需求的完整过程

| 步骤 | 谁 | 做什么 |
| :--- | :--- | :--- |
| 1 | 工程师 + AI | `req-intake`：原始材料放进 `docs/requirements/<REQ>/raw/`，生成 `intake.md`，列出澄清问题 |
| 2 | 工程师 | 向 PM 求证，把答复写进 `intake.md` |
| 3 | 工程师 + AI | `spec-change`：生成 `proposal.md`、`spec-delta.md` |
| 4 | 工程师 | 把 `proposal.md` 中的"给 PM 的确认清单"发给 PM，**本人**登记确认记录 |
| 5 | 工程师 + AI | `change-design`：生成 `tasks.md`（L 级加 `design.md`） |
| 6 | TL | L 级：审阅 `design.md`，在审批区签字 |
| 7 | 工程师 + AI | `db-migration`、`implement`：按 `tasks.md` 逐项实现 |
| 8 | 工程师 + AI | `test-accept`：补测试，填写 `acceptance.md`，本人做业务验收 |
| 9 | 工程师 + AI | `self-review`：生成自审报告；变基到最新 main，执行 `./scripts/verify.sh full` 后推送功能分支 |
| 10 | TL | 合并前复核（见下节） |
| 11 | TL | 发布、打包（`release-pack`）；运维部署后回填回执 |
| 12 | 工程师 | 归档：规格增量合并进 `docs/specs/`，变更包移到 `docs/changes/archive/` |

## 合并前复核（TL）

```bash
git fetch origin
git switch -c review/<REQ> origin/feat/<REQ>
./scripts/verify.sh full
```

1. 阅读变更包：规格增量、PM 确认记录、设计（L 级）、验收报告中每条 AC 的证据。
2. 阅读改动：`git diff origin/main...HEAD`；重点看迁移脚本、契约、权限相关代码。
3. 有意见时写在 `design.md`（或 `acceptance.md`）末尾的"复核意见"，通知工程师修改。
4. 通过后合并：

```bash
git switch main && git pull --ff-only
git merge --no-ff origin/feat/<REQ> -m "Merge feat/<REQ>" -m "Refs: <REQ>"
git push origin main
```

合并提交的提交人即为复核记录。

## 提交说明

```text
feat(visitor): 新增访客预约审批流

- 新增迁移脚本 V202610151400，存量预约默认免审
- 实现审批通过与驳回接口

Refs: REQ-20261015-visitor-approval
AI-Assisted: claude-code
```

- 类型：`feat`、`fix`、`refactor`、`perf`、`test`、`docs`、`build`、`chore`、`revert`；描述用中文。
- `Refs` 必填，S 级也要关联需求或缺陷编号；使用了 AI 时写 `AI-Assisted`。

## 门禁一览

| 时机 | 检查 | 能否绕过 |
| :--- | :--- | :--- |
| `git commit` | 基线托管文件、迁移脚本、密钥、AI 配置一致性、提交说明 | 能（`--no-verify`） |
| `git push` | 只有 TL 能推 main；`./scripts/verify.sh quick` | 能 |
| TL 合并前 | `./scripts/verify.sh full`：含集成测试、测试删除检查、升级路径测试 | **不能**，这是真正的关口 |
| 服务端钩子（可选） | 只有 TL 能推 main；提交必须有 `Refs`；已合并迁移脚本不可修改 | 不能 |

## 多人与多 Agent 并行

- 一个需求一个分支、一个变更包；不同需求尽量不改同一模块。
- 迁移脚本版本号用"年月日时分"，多人并行不会撞号；合并时出现顺序交错由 Flyway 的 `out-of-order` 处理。
- 同一个分支上不要同时开多个 AI 会话修改代码。
