# AI Native Engineering 项目官网

官网位于 `website/`，使用 Vue 3、TypeScript 和 Vite。它介绍仓库已有的 AI 协作工程基线，并提供研发手册和原版图文培训内容的阅读入口。

线上官网：<https://ane.wanghuanlab.com/>。服务器目录、配置、验证和回退方式见 [部署记录](DEPLOYMENT.md)。

## 本地开发

需要 Node.js 22+。从仓库根目录进入官网目录后安装锁定依赖：

```bash
cd website
npm ci
npm run dev
```

开发地址为 `http://127.0.0.1:5173`。端口已启用 `strictPort`，被占用时应先处理已有进程。

## 构建与预览

```bash
npm run build
npm run preview
```

构建先执行 TypeScript 检查，再生成静态文件到 `website/dist/`；预览地址为 `http://127.0.0.1:4173`。这些命令只在本地构建和预览，不会自动上传、部署或发布。

## 内容来源

- 文档阅读器在构建时直接读取仓库根目录的 `README.md`、`CHANGELOG.md` 和 `handbook/*.md`，正文以仓库文件为维护源。
- 流程与角色文案位于 `src/content.ts`，应随手册和实际校验脚本一起核对，尤其注意 PM 确认、TL 审批、工程师验收及自动门禁的能力边界。
- `scripts/training-assets.ts` 在开发时提供 `/training/`，在构建时输出 `training/index.html` 和 `training/assets/` 中的全部文件。
- 培训入口 HTML 仅将指向上级 Markdown 手册的链接改为官网的 `?doc=` 阅读入口；不修改仓库中的原文件。独立交互图 HTML、JSON 和已有验证记录均按原始字节复制，保留证据对应关系。

培训图的变更应遵循 `handbook/training/README.md` 中的生成与验证流程，不要直接修改已验证图形后沿用旧回执。

## 静态部署

将 `website/dist/` 的全部内容部署到站点根目录，并保留 `assets/`、`training/` 及其内部目录结构。服务器应优先返回真实静态文件，为普通应用路径提供回退到根目录 `index.html` 的规则；`?doc=...` 查询参数必须保留。`/training/` 应默认返回其自身的 `index.html`，缺失的静态资源应返回 404。

例如 Nginx 的站点配置可按以下思路设置，`root` 替换为实际的 `dist` 发布目录：

```nginx
root /path/to/website/dist;
index index.html;

location ^~ /training/ {
    try_files $uri $uri/ =404;
}

location ^~ /assets/ {
    try_files $uri =404;
}

location / {
    try_files $uri $uri/ /index.html;
}
```

建议每次发布保留上一份完整 `dist`，需要回退时切回上一份静态产物。官网没有后端部署步骤，也不会在构建时改动工程基线或业务项目。
