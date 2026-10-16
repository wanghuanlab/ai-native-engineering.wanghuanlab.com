**ds-meta-ai-baseline：现有设计评估与落地建议**

| 项 | 内容 |
| :--- | :--- |
| 日期 | 2026-10-15 |
| 提出方式 | 基于当前工作区的工程审查与方案评估 |
| 类型 | 流程 / 门禁 / 骨架 / 模板 / 交付 |
| 状态 | 待评审；以下为建议，不代表已批准或已实现 |
| 已确认背景 | 30+ 工程师、多业务项目；Java / Spring Boot / JPA、Vue 3；裸 Git、无 PR/MR 和 CI、无专职测试；客户现场私有化交付 |

**结论：整体方向合理，应保留现有架构；先修复关键验证缺口，再做小组试点。当前尚不具备全中心直接推广的充分依据。**

当前工程已经具备规范手册、变更包、AI 规则源、脚手架、前后端骨架与门禁脚本，超出了一个简单启动模板。最值得保留的是“业务项目独立演进、工程规范按版本同步”的定位。主要问题是部分文档把规则描述成了已经可靠实现的保障，而实际脚本只能覆盖其中一部分。

评估基于当前文件内容。根目录没有 `.codegraph/`，未使用 CodeGraph；根目录没有 `.git`，本次没有核验基线发布标签与历史。没有修改工程实现、安装依赖、启动服务或重新执行全量自测。

**一、现有设计中值得保留的部分**

| 设计 | 评价与适用边界 |
| :--- | :--- |
| 一个基线仓库，各业务系统各自一个仓库 | 适合你们多个独立交付项目；每个业务仓库内统一管理前端、后端、契约、迁移、部署 |
| 模块化单体 + Maven 模块 + 模块公开 API | 适合多数管理系统；减少跨服务部署与事务复杂度，后续按真实需求拆服务 |
| 统一 Java / Vue / TypeScript，信创和大屏作为可选画像 | 可以共享工作方式；数据库驱动、三维资源与性能指标仍需分别验证 |
| OpenAPI 先行，前后端生成代码 | 减少 AI 自行猜接口；仍需真实 HTTP 契约测试和接口兼容检查 |
| JPA validate + 增量数据库迁移 | 保留；表结构不能依赖 ORM 自动修改 |
| S/M/L 分级、变更包、BR/AC 编号 | 方向正确；需要消除规则冲突并增加轻量机器检查 |
| 一份 AI 规则源生成不同工具入口 | 保留；生成一致不等于每个模型都能正确遵守，需要任务样例验证 |
| 基线托管 / 项目自有 / 共同维护三类文件 | 保留；要补模板升级演练和项目自有基础代码的修复回流 |

**二、推广前应解决的具体问题**

以下 P1 表示对相应场景具有高影响，应在试点或交付准入前处理；P2 表示下一轮应补齐。不表示每一项都已经导致了生产事故。

**1. P1：前端检查失败可能被报告为通过，已做故障注入复现。**

[verify.sh:16](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/verify.sh:16) 用 `if "$@"` 调用检查函数；[verify.sh:46](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/verify.sh:46) 中多条前端命令依赖 `set -e` 中止。Bash 条件调用上下文使这里的失败中止行为失效，前面的错误可能被后续成功状态覆盖。

在临时目录中原样提取 `step` 和 `run_frontend`，只将 `pnpm typecheck` 模拟为退出码 23，其余 pnpm 命令成功，得到：

```text
▶ 前端检查
SIMULATED TYPECHECK FAILURE
继续执行 lint / format / test
✓ 前端检查
最终退出码：0
```

建议每条命令显式检查退出状态，失败立即返回；对生成、类型、Lint、格式、测试和构建分别注入失败，要求统一入口返回非零。门禁必须测试“能拒绝坏结果”，不能只测试正常项目能通过。

**2. P1：主干合并与检查结果没有绑定。**

[协作流程:33](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/docs/context/collaboration.md:33) 先验证功能分支，[同文件:44](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/docs/context/collaboration.md:44) 再更新 main、合并、直接推送。若 main 中间变化，最后的组合没有完整验证。[同文件:72](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/docs/context/collaboration.md:72) 将 TL 本地校验称为“不能绕过”，表述不成立。

[服务端钩子:25](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/tools/server-hooks/pre-receive:25) 只处理 main；技术负责人名单为空时身份检查不生效，使用共享 SSH 账号时 `$USER` 也无法区分个人。当前服务端钩子不核验完整测试证据。

裸 Git 可以继续使用，但建议服务端保护 main、release 分支和发布标签，使用可识别个人的认证映射。合并流程改为“同步 main → 创建最终候选合并提交 → 对该提交执行 full → 推送该提交”；远端有新提交则重新合并验证。记录提交 SHA、检查工具版本、日志和产物摘要。服务端 `pre-receive` 可以拒绝引用更新，但测试与审批证据需要另行实现，不能认为安装钩子就自动具备这些能力。[Git 官方钩子文档](https://git-scm.com/docs/githooks)

**3. P1：数据库升级测试与现场执行机制不同。**

[upgrade-path.sh:28](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/upgrade-path.sh:28) 在空库执行旧 SQL 和新增 SQL；[pg.sh:31](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/lib/pg.sh:31) 使用 psql。它没有覆盖 Flyway 历史表与校验和、代表性旧数据、目标应用行为。例如给有数据的表新增无默认值非空列，空表验证可能成功，现场迁移却失败。

建议保留 SQL 快速检查，同时增加与生产一致的“旧版本真实迁移 → 旧数据样本 → 目标版本 Flyway 升级 → JPA 校验 → 数据与接口断言”。Flyway 的校验依赖实际执行历史和校验和，不能由直接执行 SQL 替代。[Flyway Validate 官方文档](https://documentation.red-gate.com/flyway/reference/commands/validate)

**4. P1：当前规格发布后才更新，容易让并行需求依据过期信息开发。**

[流程规则:35](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/.ai/rules/10-workflow.md:35) 要求发布后才把增量合并进当前规格，[规格 Skill:22](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/.ai/skills/spec-change/SKILL.md:22) 又从当前规格的最大编号继续取号。A 已合并但未发布时，B 可能仍读旧规格、分配相同 BR/AC 编号，甚至覆盖 A 的业务规则。

建议 `docs/specs` 表示所在分支代码的规格，随代码在同一合并提交更新；发布标签保存该版本规格，客户台账指向具体标签。变更包保留增量、决策和验收历史。并行需求登记所依据的规格版本及互相依赖，合并前检查编号和语义冲突。

**5. P1：跨机器升级基线的来源不稳定，升级保真尚缺实证。**

[new-project.sh:29](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/bin/new-project.sh:29) 将本机绝对目录作为 Copier source；现有自测项目也记录了本机路径。同事克隆项目后不一定能访问同一路径。[sync-baseline.sh:25](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/sync-baseline.sh:25) 直接使用历史 source 更新。

建议正式创建使用团队可访问的基线 Git SSH URL 和固定 tag，本地目录仅用于开发模板。自测增加 vA → vB 的 Copier 更新，覆盖项目源码保留、共同维护文件冲突、被删除的示例、项目规则、失败恢复。当前 `selftest.sh` 的 upgrade_tests 是数据库升级测试，没有实际执行 Copier 更新。Copier 官方说明更新依赖版本化模板和答案文件，并可能产生需要处理的冲突。[Copier 更新说明](https://copier.readthedocs.io/en/stable/updating/)

**6. P1（相应项目交付前）：信创与安全能力需有明确准入条件。**

信创配置已诚实标注“验证通过前不得用于交付”，应保留该限制。现有信创自测生成了 DM 配置，但数据库集成测试仍使用 PostgreSQL。不能把“三种模板画像通过”解释为“PostgreSQL、达梦、金仓都验证通过”。需要记录 JDK、Boot、Hibernate、JDBC、Flyway 适配、数据库版本、操作系统及 CPU 架构的完整组合，并在目标数据库上执行测试。

不做公共用户权限业务模块是合理边界，但交付基线仍应统一认证接入接口、匿名请求默认拒绝、操作人审计、后台任务身份和权限测试。当前 `CurrentUser.id()` 未取得身份时返回系统用户 0，项目认证接入应是明确的投产前置项。单租户与多租户需立项选择，不应强制所有项目加租户字段，也不能只加字段就声称已隔离。

此外，[手册:453](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/handbook/00-方案全文.md:453) 把“代码不出公司”和“不出境”都归为可用国内云的受限类，逻辑不一致。应分别记录数据能否离开公司网络、允许地域、批准服务端点和允许上传的数据类型；国内云仍可能位于公司网络之外。

**7. P2：文档中的部分门禁尚未成为机器能力。**

[verify.sh:71](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/verify.sh:71) 没有变更包完整性、审批对象版本、AC 与证据关联、API 兼容性、依赖漏洞扫描和浏览器端到端检查。契约兼容性缺失已在 CHANGELOG 记录；其他项目也应明确区分“已自动检查 / 人工检查 / 待实现”。

建议新增轻量变更元数据校验，逐步接入契约差异检查、依赖与许可证清单、核心用户流程测试。测试数量/skip 扫描只能发现部分退化，无法判断断言语义；[checks.py:185](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/lib/checks.py:185) 的任意非空环境变量豁免应缩小到指定需求、测试文件和获批版本。

**8. P2：交付包与“通过验证的版本”之间还缺证据和现场演练。**

[release-pack.sh:16](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/release-pack.sh:16) 已检查干净工作区和标签指向 HEAD，值得保留；[同文件:24](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/scripts/release-pack.sh:24) 随后跳过测试重新打包，没有验证结果关联检查。已有 checksum 也不能证明这个包就是已测试产物。

建议交付包带 manifest：提交、基线版本、依赖锁摘要、验证记录、数据库迁移集合、镜像 digest 与架构。构建一次，对实际产物完成验证后交付；增加生产 Compose、环境变量样例、健康检查、备份恢复和升级命令，并在干净离线环境演练。当前 Compose 只覆盖本地数据库；前端 Dockerfile 只复制 admin，大屏需单独部署目标。

**三、建议的工程组织与技术统一方式**

部门基线继续维护现有 `handbook / template / bin / tools / proposals` 结构，增加兼容性矩阵、模板升级测试和门禁故障注入测试即可。业务项目保留以下结构，标注“新增建议”的项分阶段补齐：

```text
<业务项目>/
├── .ai/                       # rules、skills、项目扩展规则
├── .baseline/                 # 来源 URL、版本、画像、文件归属
├── docs/
│   ├── requirements/          # 原始需求、澄清记录
│   ├── specs/                 # 与本分支代码一致的当前规格
│   ├── changes/<REQ>/         # 提案、规格增量、PLAN、任务、验收
│   │   └── change.yaml        # 新增建议：可校验元数据
│   ├── adr/                   # 架构决策与偏离基线的理由
│   ├── context/               # 术语、模块边界、owner、踩坑
│   └── releases/              # 发布说明和客户版本台账
├── contracts/openapi/         # 接口唯一来源
├── backend/
│   ├── app/                   # 启动与装配
│   ├── common/                # 小而稳定的技术公共代码
│   └── modules/<业务模块>/    # api / web / service / domain / infra
├── frontend/
│   ├── apps/admin/            # 管理系统
│   ├── apps/screen/           # 按需大屏
│   └── packages/api-client/   # 生成客户端和手写传输适配
├── db/migration/<方言>/
├── tests/                     # 新增建议：跨系统 E2E、升级样本和交付冒烟
├── deploy/                    # 本地、生产、镜像、运维脚本
└── scripts/                   # 统一生成、检查、合并、发布入口
```

文件所有权应落实到匹配规则：工程规则、门禁由基线维护；业务规格、代码、迁移由项目维护；根 POM 与包清单共同维护并三方合并。项目自有基础代码也可能出现通用缺陷，因此基线发布时需说明哪些项目应应用补丁、谁负责验证和何时完成；“复制后归项目”不能意味着以后无人通知修复。

| 领域 | 建议统一内容 | 允许项目差异 |
| :--- | :--- | :--- |
| Java 后端 | Java 21、经验证的 Boot/BOM、模块边界、错误结构、ID/时间/分页约定 | 业务模块划分、领域模型、必要外部适配 |
| JPA | validate、关闭 OSIV、事务边界、N+1 防范、复杂 SQL 隔离到 infra | 报表、批处理等允许评审后的专用 SQL，避免为坚持 ORM 牺牲清晰度 |
| 前端 | Vue 3 + TS、统一组件库、路由、状态和 API 生成方式 | 大屏单独应用及资源加载策略 |
| 格式与质量 | Spotless、Prettier、ESLint、架构检查；统一入口执行 | 经记录的项目特例，不能靠随意关闭规则实现 |
| 数据库 | 一个项目明确目标方言，版本化迁移、升级测试 | 信创需真实验证；专有能力限定在明确画像 |
| 运行环境 | 工具链清单、pnpm 锁文件、BOM、镜像 digest、内部依赖镜像 | 客户规定的操作系统、架构及离线条件 |

版本选择以完整兼容组合为依据。当前模板选用 Spring Boot 4.1.1 与 Java 21，Java 21 在该版本官方 Java 兼容范围内；这不能替代 Hibernate、数据库驱动和迁移适配器的联合验证。[Spring Boot 官方系统要求](https://docs.spring.io/spring-boot/system-requirements.html)

前端 package.json 中存在 `^`/`~`，模板没有随附依赖锁；不同日期初始化可能解析到不同依赖。建议基线发布固定一份经过验证的依赖集合，新项目生成锁文件并提交，日常验证与发布采用冻结安装；升级通过明确变更执行。对信创环境同步验证镜像实际可运行，跨架构构建成功本身不足以证明兼容。

**四、从需求到部署的建议闭环**

```mermaid
flowchart LR
  A[需求入库与澄清] --> B[规格与验收标准确认]
  B --> C[PLAN 与影响分析]
  C --> D[契约和迁移设计]
  D --> E[实现与测试]
  E --> F[验证最终合并提交]
  F --> G[构建并验证交付产物]
  G --> H[部署与回执]
  H --> I[客户台账与改进回流]
```

| 环节 | 必须有的输入输出 | 放行依据 |
| :--- | :--- | :--- |
| 需求入库 | 原始材料、来源、目标用户、问题、范围、非目标 | 歧义已澄清，未确定内容显式列出 |
| 规格 | BR 业务规则、AC 验收标准、异常/边界/权限、适用的非功能指标 | PM 确认具体版本；记录原始回复引用，工程师登记 |
| PLAN | 输入版本、影响范围、方案与取舍、迁移/接口兼容、任务、验证、回退 | M 工程师确认；L 由 TL 审阅涉及的设计 |
| 实现 | 小任务、明确文件边界、依赖顺序、单项验证命令 | 代码、契约、迁移、规格、测试同步变更 |
| 验收 | 每条 AC 对应测试或人工证据 | 真实执行记录；高风险项由另一名工程师或 TL 复核 |
| 合并 | 最新主干上的最终候选提交 | 对该提交验证通过、owner 复核完成，远端变化重新验证 |
| 发布 | 已验证提交和构建产物、版本与兼容信息 | 制品验证通过，manifest 与说明齐全 |
| 部署 | 同一制品、配置、备份、升级路径 | 健康检查与核心业务冒烟通过，回执登记 |

不需要重复增加一个独立的 PLAN.md：现有 `design.md + tasks.md` 即可承担 PLAN。建议固定字段：`baseCommit`、`specRevision`、需求与 AC、允许/禁止修改范围、受影响模块、数据与 API 变更、兼容策略、任务依赖、验证命令、回退限制、待决问题。

`change.yaml` 只保存机器需要的元数据，Markdown 继续记录背景和推理，避免重复维护两份需求正文。元数据可包含 ID、级别、状态、相关能力、基准版本、依赖变更、AC 列表、批准内容摘要和证据索引。建议状态为 Draft → Ready → Implementing → Verified → Merged → Released，并支持 Blocked / Cancelled。

校验器负责检查文件、引用、编号、状态转换条件和批准对象是否变化；**不能仅靠扫描 Markdown 证明批准人身份**。审批应来自真实人的受控记录，AI 可以整理已有证据，不能自行产生批准。规格或设计实质变化后，原有批准应失效并重新确认。

继续保留轻量 S 级：规范提交、需求/缺陷编号、修改范围、必要验证即可。修正 [核心规则:28](/Users/wanghuan/Documents/wanghuanlab/ai-native-engineering.wanghuanlab.com/template/.ai/rules/00-core.md:28) 对“没有变更包”一概停下的要求；已在批准计划内的依赖、字段和范围无需重复询问，超出计划才升级决策。

**五、数据库迭代与多客户版本管理**

1. 表结构只通过迁移修改；已经进入受保护历史或部署过的迁移不可重写。记录版本、校验和与适用数据库。
2. 提供迁移编号生成器和冲突检查。分钟时间戳会重复，秒级也不能绝对保证唯一；合并前仍需检查并处理尚未发布脚本的冲突。
3. 破坏性变更按扩展 → 数据迁移 → 收缩分阶段进行，并覆盖客户仍在运行的旧应用兼容需求。回滚应用与回滚数据是两件事，需要分别定义。
4. 默认使用有序迁移；多客户 hotfix 如果需要乱序，逐项说明前置条件和不同升级顺序的验证结果。当前全局 `out-of-order: true` 不能证明顺序安全。Flyway 该选项仅允许补执行较低版本迁移。[官方设置说明](https://documentation.red-gate.com/fd/flyway-out-of-order-setting-277579015.html)
5. 新装、每个受支持在用版本的升级、代表性旧数据、失败重试和恢复都要有验证路径；在用版本特别多时可明确支持窗口与分段升级方案，但不能悄悄漏测客户版本。
6. 大表回填应分批、可观测、可重入，预估锁等待与停机窗口；并发建索引要连同 Flyway 事务和锁设置一起验证。Flyway 对 PostgreSQL 并发索引有具体锁配置要求。[官方 PostgreSQL 说明](https://documentation.red-gate.com/flyway/reference/database-driver-reference/postgresql-database)
7. 同名方言脚本只证明文件齐全，不证明结果一致；在真实目标库校验约束、时间、布尔值、分页、乐观锁、软删除与关键查询。

例如“预约新增审批状态”：先新增兼容字段并规定存量记录的业务值，验证旧记录仍可核销；再上线新逻辑；确认受支持旧版本不再依赖旧结构后，才删除旧列或旧逻辑。不能只测新建一条预约成功。

**六、测试、发布与 30+ 人组织方式**

没有专职测试时，仍要分开实现责任与高风险验证责任。工程师负责交付，AI 辅助生成与执行测试；权限、金额、存量数据、客户升级等由另一名工程师或 TL 复核。换一个 AI 自审有价值，但不能替代独立的业务预期和真实执行证据。

测试按风险组织：领域单测覆盖状态和业务规则，真实数据库集成测试覆盖持久化与事务，HTTP 测试覆盖契约和权限，浏览器测试覆盖少量关键用户旅程，升级测试覆盖历史客户。管理系统验收增加并发量、响应时间和数据规模；数字孪生增加目标设备、场景复杂度、首屏时间、帧率和显存预算。阈值由项目场景确认。

裸 Git 阶段建议使用一台受控验证工作机或受控执行脚本，在隔离工作区检查最终候选提交；避免在 Git 服务账号下直接运行项目任意构建代码。第一阶段不必先建设完整 CI 平台，但本地钩子不能成为唯一保障。后续若决定引入代码评审平台/CI，可复用统一脚本和证据格式。

建议指定 2～3 名固定基线维护者，每个项目有 TL 和备份人，模块 owner 负责常规评审；TL 聚焦跨模块、数据库、安全及例外决策。这是一项组织建议，需按实际项目数量安排，不要求新增独立部门。

基线维护按版本发布：版本变化、兼容矩阵、升级说明、已知限制和回退方式齐全。通用权限、工作流、文件管理等公共能力先明确接口；有多个真实项目验证且维护归属清晰后，再决定提取版本化组件。大屏资源、GIS 或复杂报表也按画像扩展，避免第一版承担全部业务领域。

**七、落地次序与验收标准**

时间为建议安排，实际取决于维护投入和信创环境可用性；以完成标准作为推广依据。

| 阶段 | 建议安排 | 重点工作 | 完成标准 |
| :--- | :--- | :--- | :--- |
| 第一阶段 | 第 1～2 周 | 修门禁错误、保护 Git 引用、验证最终合并提交、修规格同步、稳定基线来源 | 任一步失败必拒绝；他人机器能生成/升级；并行需求合并不丢规格 |
| 第二阶段 | 第 3～4 周，3～5 人试点 | 完成一个管理系统小里程碑，加入变更校验、真实升级测试、核心 E2E、离线交付演练 | 实际经历新增需求、需求变化、缺陷修复、发布、升级和恢复 |
| 第三阶段 | 第 5～8 周，按环境推进 | 信创、大屏分别验证；模板 vA→vB 更新；第二个业务项目接入 | 每个声称支持的画像有可复查验证结果，项目业务改动在升级中保留 |
| 推广阶段 | 达到前述条件后 | 按项目分批接入、培训、定期基线升级 | 合并与交付可追溯，维护与例外流程稳定运行 |

建议跟踪需求交付周期、首次验证通过率、返工原因、评审等待、逃逸缺陷、客户升级成功率和基线升级耗时。AI 生成比例或代码行数不适合作为主要绩效指标。

**八、本次验证范围**

- 实际执行：5 个 Python 脚本语法解析、15 个 Bash 脚本语法检查，全部通过。
- 实际执行：现有 default / minimal / xinchuang 三个生成项目的 AI 配置一致性与迁移静态检查，共 6 项，全部返回 0。
- 实际执行：前端 typecheck 失败注入，复现统一校验入口仍返回成功。
- 已读取但未重跑：`.selftest` 中现有后端报告共 37 个测试，记录为零失败、零错误、零跳过；这仅是已有报告，不能替代本次完整构建或证明信创数据库已验证。
- 未验证：全量自测、真实达梦/金仓、Copier 跨版本更新、生产部署、离线与 ARM 运行。上述限制已纳入建议的准入条件。

本次产出为评估与建议，没有改变现有业务代码、模板或门禁行为。
