# ane.wanghuanlab.com 部署记录

官网地址：<https://ane.wanghuanlab.com/>

首次发布完成于 2026-10-23 10:36:45（Asia/Shanghai），通过本机已配置的 SSH 连接 `root@wanghuanlab.com`，部署到现有 1Panel / OpenResty 站点。

## 当前发布

| 项目 | 值 |
| --- | --- |
| 版本目录 | `/opt/1panel/www/sites/ane.wanghuanlab.com/releases/20261023T023557Z` |
| 站点根入口 | `/opt/1panel/www/sites/ane.wanghuanlab.com/index`，软链指向上述版本 |
| 站点配置 | `/opt/1panel/www/conf.d/ane.wanghuanlab.com.conf` |
| OpenResty 容器 | `1Panel-openresty-4YeZ` |
| 发布包 SHA-256 | `26bbd4d80dd9915ab678ebc88282c2bf710fa21a2be93bfc3924e1e20ecff3e0` |
| 首页 SHA-256 | `6bf639c506a88688327c3df0d45c756b1ce6b61fa3d1e6d595d184eee305d06a` |
| 备份目录 | `/opt/1panel/www/sites/ane.wanghuanlab.com/.deploy-backups/20261023T023557Z` |

证书、HTTPS 跳转、日志路径和站点名称沿用现有 1Panel 配置。发布只增加本域名的静态路由、缓存和 gzip 配置；通过 `nginx -t` 后平滑重载。

## 路由与缓存

- 首页及普通应用路径回退到 `index.html`，保留查询参数，用于 `?doc=...` 手册入口。
- HTML 使用 `Cache-Control: no-cache`。
- `/assets/` 中带哈希的资源缓存一年，缺失文件返回 404。
- `/training/` 保留独立目录首页，缺失文件返回 404。
- `404.html` 是本次新增的品牌错误页。
- gzip 用于 HTML、CSS、JavaScript、JSON 和 SVG。

配置中的 `BEGIN AI NATIVE ENGINEERING STATIC SITE` 至 `END AI NATIVE ENGINEERING STATIC SITE` 区块属于官网静态配置。通过 1Panel 修改站点配置时应保留等价规则，运行目录保持原 `/index` 入口。

## 验证结果

- TypeScript 检查与 Vite 生产构建通过。
- 发布包摘要与服务器接收文件一致，线上首页及抽查静态文件逐字节摘要一致。
- 公网 HTTPS 正常，HTTP 自动跳转 HTTPS 并保留手册查询参数。
- HTML 缓存、哈希资源缓存、gzip、培训目录首页与缺失资源 404 均已验证。
- 线上隔离浏览器检查 52 项通过，无 JavaScript 错误；覆盖 9 阶段流程、键盘导航、质量门禁切换、创建命令与复制、9 篇手册、121 处文档/章节链接和手机导航。

浏览器截图与结果保存在本地被忽略的 `.taste-skill/production-qa/`。服务器备份目录内保存 `receipt.json`、发布前站点配置、原默认页面目录及回退脚本。

## 回退本次发布

以下命令恢复首次部署前的默认站点及原配置。脚本会先确认当前仍是本次版本，避免覆盖后续发布。

```bash
ssh root@wanghuanlab.com \
  'python3 /opt/1panel/www/sites/ane.wanghuanlab.com/.deploy-backups/20261023T023557Z/rollback.py'
```

## 后续发布

先在本地执行 `npm run build`，把 `dist/` 上传到新的独立版本目录。保留已有哈希资源，以兼容已打开页面的延迟加载；核对文件摘要与权限后，将 `/index` 入口原子切换至新版本。需要改动虚拟主机时，先备份单站点配置，通过 `nginx -t` 再平滑重载。确认公网与浏览器验证通过后记录新版本及其回退方式。
