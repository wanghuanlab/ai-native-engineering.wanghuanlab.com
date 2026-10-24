# 官网设计与验证记录

## 设计依据

受众为技术负责人、工程师、产品经理、运维实施及基线维护者。页面希望访客理解 AI 协作工程基线，并进入快速开始或角色手册。

项目特有材料：仓库内规格、变更包、S/M/L 分级、8 个标准 Skills、一源多工具规则、quick/full 校验、人工确认与审批、契约生成、一次复制的工程骨架、按版本同步的基线、信创数据库方言、现场部署回执。

页面主张与依据：

- 协作具有工程依据：展示真实变更包文件及用途。
- 多工具遵循统一规则：展示 `.ai/rules` / `.ai/skills` 到各工具配置的生成关系。
- 从需求走向交付：提供可选择的 9 阶段产物、完成条件与责任说明。
- 质量要求可执行：展示真实 quick/full 校验范围，保留人工验收及升级校验边界。
- 项目可以独立演进：展示技术骨架和基线同步的文件归属。
- 每个角色知道下一步：提供仓库手册的直接阅读入口。
- 新项目可以开始：按真实项目代号校验生成平台对应命令。

## 视觉方向

采用 design-taste-frontend 的 The product performs，seed `1641318164`。

在这个页面上，变更包与规则源成为可阅读、可操作的工程标本。项目现有的源码与手册是视觉材料；变更包切换、流程选择、校验范围切换与命令生成构成可操作演示，明确标注为结构或范围说明。

石墨黑、冷白与工程蓝沿用用户认可的提示词。主要字体使用系统中文无衬线字体，代码使用系统等宽字体。真实内容保持可读，动效使用轻量入场及内容切换，并提供 reduced-motion 回退。

方向调整及原因：最初抽取的窄栏小标题 hero 与用户明确要求的大标题、非对称首屏冲突，重抽 hero；features 改为文字与局部片段，避免把真实内容硬塞进重复卡片。最终以用户的非对称首屏、角色文档和快速开始要求为准。未使用需要虚构客户的 Logo proof。

## 视觉检查

ROUND 1
Seen in one second: 左侧两行主张与右侧可切换的规格文件。
Idea (one sentence): 以真实工程产物把 AI 协作的规则和交接可视化。
Live thing: 变更包切换、9 阶段流程、校验范围切换、项目创建命令。
Layout words by section: hero=非对称片段 / intro=文字列 / collaboration=深色规则图 / workflow=列表与细节 / quality=命令范围 / foundation=技术表 / handbook=角色入口 / start=命令生成。
Scores: design 7.0 · usability 7.5 · creativity 7.0 · content 8.5 → overall 7.3
Caps applied: 初轮字号与角色卡片检查失败，修复后重新检查。
Top three problems:
1. 手机流程条末尾换行（mobile-page-01）：缩小间距，保持完整主线。
2. 角色入口过于重复（desktop-page-02）：改为全宽角色索引。
3. 辅助文字与正文层级过多：合并字号，提高正文及前置条件说明的字号与对比。

ROUND 2
Seen in one second: 大标题与规格产物，工程内容保持主体。
Idea (one sentence): 用可操作的真实产物说明基线如何协作。
Live thing: 可切换的流程与可复制的真实命令。
Layout words by section: hero=非对称片段 / intro=文字列 / collaboration=深色规则图 / workflow=流程索引 / quality=命令范围 / foundation=技术表 / handbook=全宽角色索引 / start=命令生成。
Scores: design 7.5 · usability 8.0 · creativity 7.0 · content 8.5 → overall 7.7
Caps applied: 自动检查将最长的前置依赖说明识别为正文，该处仍为13px，已提高到16px。
Top three problems:
1. 前置依赖说明应更易读：提高字号与对比。
2. 文档导航装饰与首页不一致：移除装饰编号、英文小标签与细线。
3. 复制检查应等待内容切换结束：浏览器验证等待稳定状态。

## 素材与边界

官网未使用外部图片、视频、第三方客户标识或虚构业绩。局部工程界面均由本仓库真实文件与规则构成，外部摄影与视频对这个工程基线没有可验证的说明价值。原有图文培训内容来自 `handbook/training/`，独立图 HTML 保持原字节，现有验证记录保留在原目录。

所有品牌表达是本官网设计；流程与校验范围说明不表示某次真实执行已成功，也不代替 PM 确认、TL 审批或工程师人工验收。

## 最终检查

ROUND 3
Seen in one second: 两行工程主张与可阅读的规格文件。
Idea (one sentence): 让工程产物成为官网的视觉材料与互动入口。
Live thing: 文件切换、流程选择、校验范围切换、真实命令生成与复制。
Layout words by section: hero=非对称片段 / intro=文字列 / collaboration=深色规则图 / workflow=流程索引 / quality=命令范围 / foundation=技术表 / handbook=全宽角色索引 / start=命令生成。
Scores: design 7.5 · usability 8.0 · creativity 7.0 · content 8.5 → overall 7.7
Caps applied: 无未解决的测量失败项。评分为内部视觉自评。
Top three problems:
1. 没有适合说明该基线的摄影或视频，保留真实工程片段。
2. 手机技术表的填充行被自动检查视为重复卡片；保留，因为它对应真实技术分类，且与角色索引和流程区构图不同。
3. 未发现新的布局、溢出或内容遮挡问题。

- 源码风格检查：0 FAIL / 0 WARN。
- 首页 1440 / 768 / 390px 检查：0 FAIL，3 个已说明原因的 WARN（无摄影、无视频、手机填充表行）。
- 隔离 Chrome 浏览器交互检查：52 项通过，无 JavaScript 错误；包括 9 阶段流程、键盘导航、quick/full 切换、真实命令、剪贴板输出、无效项目代号、9 篇文档、121 处文档与章节链接、手机导航和培训图入口。
- TypeScript 检查与 Vite 生产构建通过。
- 既有培训资产保留在仓库中，构建输出保持原字节。

截图和机器检查结果保存在被忽略的 `.taste-skill/inspect/` 与 `.taste-skill/qa/`，不进入发布源码。
