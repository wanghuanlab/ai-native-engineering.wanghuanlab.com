# ane-plugin-admin

认证与权限插件，源码注入到使用本基线的项目里。范围是用户、角色、菜单、部门、岗位、验证码和 JWT 登录。

初始管理员用户名在安装时指定，默认 `admin`，初始密码是 `Admin@123`。生产环境登录后应立即修改，并用环境变量 `ADMIN_JWT_SECRET` 覆盖开发用的令牌密钥。

本地需要 Redis。`deploy/local/compose.yaml` 会增加一个 `redis:7-alpine`，端口 6379。

数据权限用 JPA `Specification`：`ALL`、`DEPT_AND_CHILD`、`CUSTOM`、`DEPT`、`SELF`，多个角色取范围更宽的一个。`ane.admin.data-scope-enabled=false` 时不再过滤。
