# Java 编码与质量门禁

本基线不把某一本手册当成全部编码规范。人和 AI 写的代码走同一套门禁：排版由工具改对，结构、缺陷、安全和架构由检查直接失败。

条文在创建项目时随模板复制，`new-project` 不访问外网。

## 分层

| 层 | 采用什么 | 怎么生效 |
| :--- | :--- | :--- |
| 代码应该长什么样 | Google Java Style 的命名、文件组织和结构要求；换行以 Palantir Java Format 为准（它基于 google-java-format，长调用链更接近日常阅读习惯） | Spotless 自动格式化；Checkstyle 检查命名、括号、空 catch、星号 import 等格式化工具不管的部分 |
| Java 工程实践 | 《Java 开发手册》黄山版 1.7.1。强制项和本基线的取舍在 `.ai/rules/25-alibaba-java.md` | 写代码时遵守。官方 P3C Maven 插件最新仍是 2.1.1，绑定旧版 PMD，不能在 Java 21 上当作门禁 |
| 安全与可靠性 | SEI CERT Oracle Java 的关注点，加上 OWASP 对 Web / API 的要求 | 能扫描的部分用 SpotBugs + Find Security Bugs；其余写在 `.ai/rules/70-security.md` 和黄山版安全节 |
| 架构边界 | 模块只能依赖对方的 `api` 包；Controller 不碰仓储、不开事务 | ArchUnit、Spring Modulith，测试失败即失败 |
| 测试与覆盖率 | JUnit 5、Testcontainers。Mockito 只在需要隔离外部系统时使用，领域规则不用 Mock 代替真实对象 | `verify full` 跑单元测试和集成测试，并检查 JaCoCo 聚合行覆盖率不低于 `backend/quality/coverage-minimum.txt`。带示例模块的骨架实测约 73%，下限定为 60% |
| 质量平台 | SonarQube / SonarJava | 有服务器时用 `-Psonar`。没有服务器时，默认门禁不连接外网 |

## 推送前和合并前

推送前钩子执行 `verify quick`：

```bash
cd backend && ./mvnw spotless:check checkstyle:check test spotbugs:check
```

合并前执行 `verify full`。在上述检查之外，还有集成测试、JaCoCo、ArchUnit、迁移脚本、密钥扫描和升级路径。

格式不对时先执行 `cd backend && ./mvnw spotless:apply`，不要手改空格去迁就检查器。

不得用下面的方式让门禁变绿：

- `-DskipTests`、`spotless.skip`、`checkstyle.skip`、`spotbugs.skip`、`jacoco.skip`
- `SKIP_VERIFY=1`（钩子只给紧急情况，合并前仍然要跑 full）
- 删除或跳过测试，或把 `backend/quality/` 里的规则和覆盖率下限改松

`backend/quality/` 与本文都是基线托管文件。

## 安全编码要守的底线

CERT 与 OWASP 在本仓库里收成这些必须做到的事：

- 外部入参要校验。SQL 使用参数绑定，禁止拼接。
- 资源用 try-with-resources 关闭。不要吞掉异常，不要 `printStackTrace`。
- 不使用 `Executors` 工厂和裸 `new Thread`。`ThreadLocal` 在 `finally` 里 `remove()`。
- 金额和计数不用 `float` / `double`。主键在 JSON 里用字符串。
- 日志、异常信息和测试数据里不出现令牌、密码和个人信息明文。
- 属于某个用户的功能和数据要做权限校验。Cookie 会话防 CSRF。上传限制大小和类型。对外重定向走白名单。
- 生产环境关闭 Knife4j，对外入口不代理文档路径。

## SonarQube

默认校验不启动 Sonar。项目有质量平台时：

```bash
cd backend && SONAR_HOST_URL=https://sonar.example SONAR_TOKEN=*** ./mvnw -Psonar verify sonar:sonar
```

覆盖率使用 JaCoCo 的 XML 报告。生成代码目录已排除。质量阈由 Sonar 项目配置，不写进会在没有服务器时失败的默认门禁。
