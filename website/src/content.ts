export const stages = [
  {
    id: "intake",
    label: "入库与澄清",
    title: "先把需求说清楚",
    description:
      "把原始材料和澄清过程留在仓库中。工程师提出 S / M / L 分级建议，由技术负责人认定。",
    input: "原始需求材料、相关当前规格",
    outputs: ["raw/ 原始材料", "intake.md 澄清记录", "分级建议"],
    criteria: "问题已有答案，或明确列为本期不做；分级经 TL 认定。",
    owner: "工程师推进 · PM 回答澄清 · TL 认定分级",
    skill: "req-intake",
  },
  {
    id: "specification",
    label: "规格",
    title: "把共识写成验收依据",
    description:
      "将业务规则转成可验证的验收标准。PM 逐条确认，工程师登记真实的确认人、时间、方式与原话。",
    input: "澄清结论、当前能力规格",
    outputs: [
      "proposal.md 提案",
      "spec-delta.md 规格增量",
      "PM 确认清单与记录",
    ],
    criteria: "业务规则被验收标准覆盖；PM 已真实确认，确认记录由工程师登记。",
    owner: "工程师整理 · PM 确认业务规则与验收标准",
    skill: "spec-change",
  },
  {
    id: "design",
    label: "设计与计划",
    title: "让每项任务都有边界",
    description:
      "结合代码和上下文分析影响，将规格拆成有修改范围、执行顺序和验证命令的任务；L 级补充技术设计。",
    input: "已确认规格、代码、项目上下文",
    outputs: ["tasks.md 任务与检查点", "L 级 design.md 技术设计"],
    criteria: "修改范围与验证命令齐全；L 级设计已获 TL 审批。",
    owner: "工程师推进 · TL 审批 L 级设计",
    skill: "change-design",
  },
  {
    id: "database",
    label: "数据库",
    title: "把数据演进纳入设计",
    description:
      "依据设计新增迁移，保持已合并脚本只读，为每个启用方言提供对应文件，并从真实测试库生成结构摘要。",
    input: "技术设计、历史迁移、数据库方言配置",
    outputs: ["新增迁移脚本", "实体变更", "数据库结构摘要"],
    criteria:
      "启用方言文件齐全，完成相应数据库验证；文件规则检查不代替 SQL 实际执行。",
    owner: "工程师负责验证",
    skill: "db-migration",
  },
  {
    id: "implementation",
    label: "实现",
    title: "沿着规格逐项实现",
    description:
      "在已授权的任务范围内更新契约、后端和前端。每完成一项任务就检查改动、执行验证并记录检查点。",
    input: "任务、规格、已批准的设计",
    outputs: ["OpenAPI 契约及生成结果", "后端与前端实现", "任务状态与验证记录"],
    criteria: "逐项验证并更新任务；verify quick 通过。",
    owner: "工程师驱动 AI 并检查改动",
    skill: "implement",
  },
  {
    id: "acceptance",
    label: "测试与验收",
    title: "让每条标准都有证据",
    description:
      "为每条 AC 建立测试或操作证据。AI 可整理自动化结果与报告，人工验证和验收结论由工程师完成。",
    input: "逐条验收标准、实现结果",
    outputs: [
      "测试与实际执行证据",
      "acceptance.md 验收报告",
      "工程师人工验收结论",
    ],
    criteria: "每条 AC 有证据；工程师完成人工验收；verify full 通过。",
    owner: "工程师执行测试与人工验收",
    skill: "test-accept",
  },
  {
    id: "review",
    label: "自审与合并",
    title: "把复核留给明确的人",
    description:
      "在新会话自审规格、差异和验证证据，处理发现的问题；TL 复核 PM 确认、L 级审批、AC、迁移与契约后合并。",
    input: "变更包、代码差异、验收证据",
    outputs: ["自审报告", "问题处理记录", "TL 复核后的合并结果"],
    criteria: "问题已处理；待合并状态 full 通过；TL 完成复核并合并。",
    owner: "工程师自审 · TL 复核与合并",
    skill: "self-review",
  },
  {
    id: "release",
    label: "发布",
    title: "交付一个可部署的版本",
    description:
      "以在用客户版本为起点准备发布和升级说明。TL 审阅文档与验证结果，提交发布文档、打标签后生成交付包。",
    input: "提交、迁移、配置、客户版本台账",
    outputs: [
      "release-notes.md 发布说明",
      "deploy-guide.md 部署手册",
      "upgrade-guide.md 升级手册",
      "带校验和的版本交付包",
    ],
    criteria: "TL 已审阅；完成对应升级验证；发布文档提交并打标签后打包。",
    owner: "TL 发起、审阅与发布",
    skill: "release-pack",
  },
  {
    id: "deployment",
    label: "部署与归档",
    title: "让现场与规格保持一致",
    description:
      "运维按交付手册校验、备份、独立迁移并部署，回填真实结果；工程师合并规格增量、归档变更包，项目组更新在用版本台账。",
    input: "版本交付包、部署与升级手册",
    outputs: [
      "真实部署回执",
      "客户在用版本台账",
      "更新后的 docs/specs/",
      "已归档变更包",
    ],
    criteria: "现场版本与部署结果可查；当前规格与已发布行为一致。",
    owner: "运维实施部署 · 工程师归档 · 工程师或 TL 登记台账",
    skill: "运维部署 · 工程师归档",
  },
];

export const roles = [
  {
    id: "engineer",
    title: "工程师",
    description:
      "从需求入库到验收全程负责：驱动 AI、检查改动、保留逐条 AC 证据，亲自完成人工验收并维护任务检查点。",
  },
  {
    id: "lead",
    title: "技术负责人",
    description:
      "认定 S / M / L 分级，审批 L 级设计，复核并合并，审阅发布与升级依据，打标签交付版本。",
  },
  {
    id: "product",
    title: "产品经理",
    description:
      "提供原始材料、回答澄清问题、确认业务规则与验收标准。工程师登记确认记录，并据此执行验收。",
  },
  {
    id: "operations",
    title: "运维与实施",
    description:
      "依据交付包手册校验文件、备份数据库、独立执行迁移并部署，回填客户现场的真实版本与执行结果。",
  },
  {
    id: "maintainer",
    title: "基线维护者",
    description:
      "维护模板、规则和质量门禁，通过基线自测后发布版本，处理项目改进提案并提供升级说明。",
  },
  {
    id: "training",
    title: "团队与新人",
    description:
      "通过角色指南、交互图和完整示例学习分级、产物、AI 指令、验证与交接，建立共同的研发工作方式。",
  },
];

export const quickChecks: string[] = [
  "AI 配置与规则源一致性",
  "迁移命名、启用方言文件对应与已合并脚本不可变",
  "后端 Spotless、Checkstyle、单元测试与 SpotBugs",
  "前端 API 生成、类型、Lint、格式与测试",
];

export const fullChecks: string[] = [
  "AI 配置一致性与迁移脚本规则",
  "测试删除或减少检查、全仓密钥扫描",
  "后端 Maven verify、集成与架构测试、JaCoCo 覆盖率下限",
  "前端 API 生成、类型、Lint、格式、测试与构建",
  "台账在用版本到当前 PostgreSQL 迁移的 SQL 路径；无在用版本时明确跳过",
];
