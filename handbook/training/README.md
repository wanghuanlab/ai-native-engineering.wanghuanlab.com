# 图文培训手册

入口为 `index.html`，正文来自上一级的 `06-团队培训使用手册.md`。正文与三张 Archify 交互图都内嵌在单个 HTML 中，可复制给团队离线阅读；文末参考文档链接需要保留原仓库目录。

运行 `python3 handbook/training/build.py` 重建。构建只用 Python 标准库，支持本手册使用的 Markdown 子集；不是通用 Markdown 渲染器。

`assets/<图名>/` 保留独立图 HTML、candidate.json、交付记录、finalize 回执和浏览器检查记录。图由 Archify 3.1.0 生成，三张图均通过 validate、deliver、严格 check 和 browser-check；这些检查不等于人工视觉验收。构建时会检查 finalize 状态和独立图 HTML 的 SHA-256。

回执保留首次生成时 `.archify/` 下的原始路径，复制到 assets 不改变图的字节和证据。重新绘图时以 candidate 为源，给本次请求建立新的 `.archify/` 目录，更新 `meta.output`，重新 finalize 后再更新这里的图与回执；不能手改图 HTML 后沿用旧回执。

图展示的是当前仓库文档定义的治理与研发流程，以及脚本实现的检查职责。业务需求示例与培训时间为教学安排，不代表真实需求、审批或实测工时。
