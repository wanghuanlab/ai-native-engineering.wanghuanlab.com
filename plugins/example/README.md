# example

最小示例插件，用来验证三件事：创建项目时引入、项目建好后再引入、按标签升级。

它不是业务功能。业务项目不要勾选，也不要把它发布成生产插件。

装入之后会增加：

- 后端模块 `sample`（一条只读接口，带 `@RequiresPermission`）
- 契约 `contracts/openapi/sample.yaml`
- 迁移脚本 `V<安装时刻>__sample_create_item.sql`
- 前端页面 `src/plugins/example/`

页面上的文字 `sample-plugin-v1` 是升级测试的标记。
