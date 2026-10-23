# ai-native-engineering

元宇宙研发中心的 AI 协作工程化管理基线：统一各项目的研发流程、产物规范、工程约定、AI 协作规则和质量门禁，并提供一个可以直接运行的空骨架。

基线不包含业务功能，也不是公共 SDK。骨架代码在创建项目时复制一份，之后归项目所有；流程、规则、门禁脚本由基线托管，通过版本同步升级。

团队培训从[使用手册](handbook/06-团队培训使用手册.md)开始，也可打开含交互架构图和流程图的[离线图文版](handbook/training/index.html)。

## 创建项目

需要：Python 3.10+ 与 [uv](https://docs.astral.sh/uv/)（或 `pip install copier`）、Git、JDK 21、Docker、Node.js 22+、pnpm 11。

macOS / Linux：

```bash
bin/new-project.sh ~/work/park            # 交互回答项目代号、密级、画像等问题
cd ~/work/park && ./scripts/setup.sh && ./scripts/verify.sh quick
```

Windows（本机 PowerShell 或 cmd，不需要 WSL 或 Git Bash）：

```bat
bin\new-project.cmd %USERPROFILE%\work\park
cd %USERPROFILE%\work\park
scripts\setup.cmd
scripts\verify.cmd quick
```

`new-project.ps1` 与 `scripts\setup.ps1` 等价。若 PowerShell 禁止运行脚本，用 `.cmd`，或执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。

非交互方式：

```bash
bin/new-project.sh ~/work/park --defaults -d project_code=park -d project_name=智慧园区 -d tech_lead=wanghuan \
  -d security_level=restricted -d enable_xinchuang=true -d xinchuang_db=dm -d enable_screen=true
```

创建时记录的基线来源是团队可访问的 Git 地址，并固定到标签或提交，不是某台机器上的目录。默认取本仓库 `origin`（会去掉 URL 里的用户名和令牌）；可用 `--source` / 环境变量 `BASELINE_SOURCE` 指定地址，用 `--ref`（或 `--vcs-ref`）/ `BASELINE_REF` 指定标签或提交。没有标签时固定为当前提交的完整哈希，该提交必须已经在远端上。之后在项目里用 `scripts/sync-baseline.sh <版本>`（Windows：`scripts\sync-baseline.cmd`）升级；来源不可达或仍是本机路径时会直接失败，并可用 `--source` 改掉记录的地址。

## 生成的项目包含什么

| 方面 | 内容 |
| :--- | :--- |
| 流程与产物 | S / M / L 分级；需求入库、变更包（提案、规格增量、设计、任务、验收）；10 份产物模板和一个填写完整的示范变更包 |
| AI 协作 | `.ai/rules` 与 `.ai/skills` 一份源文件，编译生成 `AGENTS.md`、`CLAUDE.md`、`.cursor/rules`，以及 Cursor、Claude Code、Codex 的 Skills 目录；8 个标准 Skill 对应流程各环节；按项目密级生成 AI 使用规则 |
| 后端 | Java 21、Spring Boot 4、JPA、Flyway、Spring Modulith 模块边界、ArchUnit 分层规则、契约生成接口、Knife4j 接口文档、ProblemDetail 错误响应、雪花 ID、软删除与审计字段、Testcontainers 集成测试 |
| 前端 | Vue 3、TypeScript、Element Plus、Pinia、由契约生成的接口客户端；可选 Three.js 大屏应用 |
| 数据库 | PostgreSQL；可选达梦或人大金仓，迁移脚本按方言一一对应 |
| 门禁 | 提交钩子、推送钩子、`verify`（`quick` / `full`）。quick 含 Spotless、Checkstyle、SpotBugs；full 另含集成测试、JaCoCo、ArchUnit。另有迁移脚本不可变、测试删除检查、密钥扫描、升级路径测试；有 SonarQube 时用 `-Psonar` |
| 脚手架 | `new-change`、`new-module`、`db-schema`、`release-pack`、`sync-baseline`。逻辑在 Python；`.sh`、`.cmd`、`.ps1` 只负责启动 |

## 目录

| 路径 | 内容 |
| :--- | :--- |
| `handbook/` | 研发规范手册：方案全文 + 各角色操作指南（从这里开始读） |
| `template/` | 项目模板 |
| `copier.yml` | 创建项目时的问题与文件归属 |
| `bin/` | `new-project`（`.sh` / `.cmd` / `.ps1`）、维护者自测 `selftest.sh` |
| `tools/server-hooks/` | 裸 Git 服务端钩子（只在 Git 服务器上运行，保持 Bash） |
| `proposals/` | 各项目对基线的改进提案 |

## 维护

修改基线后执行 `bin/selftest.sh all`（生成三种画像的项目，跑完整校验并验证门禁拦截）。只检查基线来源与一次真实的 `copier update` 时执行 `bin/selftest.sh source`。发布流程、Windows 入口和不能跨平台的部分见 `handbook/05-基线维护指南.md`，版本变化见 `CHANGELOG.md`。
