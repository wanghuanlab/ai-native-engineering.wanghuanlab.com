---
id: 25-alibaba-java
title: Java 编码规范（阿里巴巴黄山版）
scope: glob
globs: backend/**/*.java
summary: 编写或修改 Java 前读取；强制项必须遵守
---
# Java 编码规范（阿里巴巴黄山版）

依据《Java 开发手册》黄山版 1.7.1（2022-02-03）整理，供离线执行。强制项必须遵守。推荐项默认遵守，偏离时在代码注释写明原因。参考项不作为要求。

手册中的正例、反例和说明不逐字收录。分层、契约、表结构和错误响应若与本文件冲突，以 `.ai/rules/20-backend-java.md`、`30-database.md`、`40-api-contract.md` 为准。下面「本基线的取舍」优先于手册原文。

## 本基线的取舍

- 分层是 `api` / `web` / `service` / `domain` / `infra`，不是手册里的 Manager、DAO。持久化用 Spring Data Repository。模块对外接口是 `*Facade`，实现类后缀 `Impl`。
- 成功响应直接返回业务对象，没有 `00000` 错误码，也不使用 `errorMessage` 隐藏域。失败用 ProblemDetail（`code`、`title`、`detail`、`traceId`）。错误码仍是字符串：来源 `A` / `B` / `C` 加编号，号段登记在 `docs/context/architecture.md`，不随手新造。
- 契约生成的类型后缀是 `Dto`，不要改成 `DTO`。不要把类命名成 `xxxPOJO`。
- 标准列是 `id`、`created_at`、`created_by`、`updated_at`、`updated_by`、`version`、`deleted`，不是 `create_time` / `update_time`。`deleted` 是软删除标记，不加 `is_` 前缀。
- 索引名是 `pk_<表>`、`uk_<表>_<字段>`、`idx_<表>_<字段>`。
- 主键在库内是 `BIGINT`，在 JSON 里是字符串。金额在库内用 `NUMERIC`，在 Java 里用 `BigDecimal`，禁止用 `float` / `double` 记金额。
- 时间用 `java.time`（实体里是 `Instant`，时区 UTC）。禁止 `java.sql.Date`、`java.sql.Time`、`java.sql.Timestamp`，也不要新写 `java.util.Date` / `Calendar` / `SimpleDateFormat`。
- 格式由 Spotless（Palantir Java Format）和 `.editorconfig` 执行：4 空格、UTF-8、LF、括号和大括号空格、单行宽度。提交前运行 `cd backend && ./mvnw spotless:apply`。不要为了贴手册正例去手改已经被格式化的代码。
- 不在每个类上写 `@author` 和创建日期，作者以 Git 历史为准。
- JPA 实体不写 `toString()`，避免懒加载和敏感字段进入日志。对外 DTO、记录类可以有 `toString()`。
- 已启用虚拟线程（`spring.threads.virtual.enabled`）。禁止 `new Thread` 和 `Executors` 工厂方法。需要平台线程池时显式 `new ThreadPoolExecutor(...)` 并命名线程。
- MyBatis、iBATIS、`resultMap`、`${}` 拼接 SQL、MySQL 前缀索引、`ISNULL()` 不采用。原生 SQL 只放在 `infra`，参数必须绑定。

## 命名与常量

- 命名不用下划线或 `$` 开头或结尾，不用拼音、中文，也不用侮辱性或种族歧视性词语（用 `blockList` / `allowList`，不用 `blackList` / `whiteList`）。
- 类名 UpperCamelCase；方法、参数、变量 lowerCamelCase；常量全大写下划线，名字要能表达含义。
- 抽象类以 `Abstract` 或 `Base` 开头；异常以 `Exception` 结尾；测试类以被测类名开头、`Test` 结尾（集成测试沿用本基线的 `*IT`）。
- 数组写成 `int[] array`，不写成 `int array[]`。
- 包名全小写、单数、点分单词。禁止无含义缩写（不要把 `Abstract` 写成 `Abs`）。
- 父子类成员、同一方法不同代码块的局部变量，不要同名。非 setter/getter 的参数不要和字段同名。
- POJO 的布尔属性不要 `is` 前缀，也不要同时存在 `isXxx()` 和 `getXxx()`。
- 对外服务是接口，实现类加 `Impl`。
- 禁止魔法值。`-1`、`0`、`1` 可以直接出现。状态、阈值、缓存 key、正则写成常量或枚举，按功能拆开，不要堆进一个大常量类。
- `long` / `Long` 后缀用大写 `L`，`float` / `double` 后缀用大写 `F` / `D`。

## 面向对象

- 静态成员用类名访问，不通过对象访问。覆写方法加 `@Override`。
- 可变参数只在参数类型和业务含义都相同时使用，放在参数表最后，类型不要用 `Object`。
- 已被外部或二方库调用的方法签名不能改。废弃方法加 `@Deprecated` 并写明替代。不调用已废弃的 JDK 或库方法。
- 字符串比较用常量调用 `equals`，或 `Objects.equals`。整型包装类用 `equals`，不要用 `==`。
- 浮点不用 `==` 或 `Float.equals` 做等值判断。精确值用 `BigDecimal`，用字符串或 `BigDecimal.valueOf` 构造，禁止 `new BigDecimal(double)`。`BigDecimal` 等值用 `compareTo`。
- 货币以最小单位的整数，或本基线规定的 `BigDecimal` + `NUMERIC` 存储，禁止二进制浮点。
- 实体、DTO、接口入参和返回值用包装类型，不设属性默认值。局部变量可以用基本类型。
- 实体字段类型和列类型匹配：`bigint` 对应 `Long`，不要用 `Integer` 接可能溢出的主键或计数。
- 构造方法里不写业务逻辑。
- `equals` 与 `hashCode` 成对覆写。作为 `Set` 元素或 `Map` 键的对象必须覆写两者。
- 新增可序列化字段时不改 `serialVersionUID`；确需不兼容升级才改。
- 枚举常量大写，构造参数私有且不可变，每个常量用注释说明含义。类名不加 `Enum` 后缀。

## 集合、并发与控制语句

- 集合判空用 `isEmpty()`，不用 `size() == 0`。
- `Collectors.toMap` 必须传入合并函数，且 value 不能为 null。
- `subList` 的结果不要强转成 `ArrayList`；不要在遍历子列表时增删父列表。
- `keySet()` / `values()` / `entrySet()`、`Collections.emptyList()`、`singletonList()`、`Arrays.asList()` 的返回值不要增删元素。
- `toArray` 写成 `list.toArray(new String[0])` 这种类型一致、长度为 0 的形式。
- `addAll` 前判断入参不是 null。
- `? extends T` 的集合不要 `add`，`? super T` 的集合不要当作出参去 `get`。把原始类型集合赋给泛型集合后，取出元素要先判断类型。
- 不要在 for-each 里 `add` / `remove`。单线程用 `Iterator.remove()`，并发修改要加锁。
- `Comparator` 必须满足反对称、传递和相等一致，相等时要返回 0。
- 单例及其方法要线程安全。
- `ThreadLocal` 在 `finally` 里 `remove()`。
- 锁的粒度尽量小，不加在整个方法上；多资源加锁顺序保持一致。
- `lock()` 放在 `try` 之外，`unlock()` 放在 `finally`。`tryLock()` 成功后才能进入业务并在 `finally` 解锁。
- 并发更新同一行用本基线的 `version` 乐观锁，或在设计里说明的悲观锁。资金类更新用悲观锁：加锁、判断、更新、释放。
- 定时任务不用 `Timer`。
- `switch` 的每个分支用 `break` / `return` 结束，或写注释说明故意落入下一支。`switch (外部字符串)` 先判 null。
- `if` / `else` / `for` / `while` / `do` 必须带大括号。
- 三目运算符两个分支的包装类型要一致，避免 `int` 条件表达式把 `null` 的 `Integer` 拆箱。
- 高并发的循环退出条件不要用「相等」判断去等一个会被并发改掉的计数。

## 时间、正则与工具

- 日期模式里年份用 `yyyy`，不要用 `YYYY`。月份是 `M`，分钟是 `m`；24 小时是 `H`，12 小时是 `h`。
- 当前毫秒用 `System.currentTimeMillis()`，统计耗时优先用 `Instant` 或 `nanoTime`。
- 不要把一年写成 365 天。跨日、闰年用 `java.time`。
- 正则预编译为常量，不要在循环里 `Pattern.compile`。
- 属性拷贝用 MapStruct，禁止 Apache `BeanUtils` 和 Spring `BeanUtils.copyProperties`。
- `Math.random()` 的范围是 `[0, 1)`。需要密码学随机数时用 `SecureRandom`，不要用 `Random` 做令牌或密码。

## 注释

- 类、对外接口和对外方法用 Javadoc（`/** */`），写清用途、关键约束和失败时抛出的业务异常。
- 方法内单行注释用 `//`，放在代码上一行，双斜线后一个空格。多行用 `/* */`。
- 枚举常量必须有注释。契约里的枚举还要在 `description` 中写明含义。

## 异常与日志

- 能用前置条件避免的运行时异常（空指针、越界）不要靠 `catch` 来控制流程。
- 捕获是为了处理：转换为 `BizException`、补偿，或记录后重新抛出。禁止空 `catch`。事务里捕获后若需回滚，要显式回滚或继续抛出。
- `finally` 关闭资源（优先 try-with-resources），`finally` 里不要 `return`。
- 捕获类型与抛出类型匹配，或者捕获父类。调用二方库、RPC、动态生成代码时，边界处可以捕获 `Throwable`，记录后转换为业务异常或系统错误，不要把 `Throwable` 吞掉。
- 日志用 SLF4J 的占位符（`log.info("id={}", id)`），禁止字符串拼接后仍打低级别日志，禁止 `System.out`、`System.err`、`printStackTrace`。
- `trace` / `debug` / `info` 在输出前判断级别是否开启。异常日志同时带上现场信息（业务主键、关键参数）和堆栈。
- 不要把对象 `JSON` 序列化后整段打进日志。不打印个人信息、密钥和令牌。
- 生产日志至少保留 15 天；涉及网络运行、安全事件和个人信息操作的记录按法规保留不少于 6 个月。扩展日志文件名带上应用名和用途，并关闭日志向上传递（`additivity=false`）。

## 单元测试

- 遵守 AIR：自动、独立、可重复。用例之间不互相依赖，不依赖外网和人工输入。
- 测试放在 `src/test/java`，不写进 `src/main`。
- 领域规则用单元测试，粒度到类或方法。核心业务的新增代码要有对应测试。
- 本基线另外要求：测试名带 AC 编号；集成测试用 Testcontainers；禁止删除、`@Disabled` 或削弱断言。见 `.ai/rules/60-testing.md`。

## 安全

- 属于某个用户的功能和数据必须做权限校验。新增接口在 `design.md` 说明谁可以调用。
- 身份证号、手机号、银行卡号等展示脱敏，存储加密；日志和测试数据同样脱敏。
- 任何外部入参都要校验（Jakarta Validation 或显式判断）。SQL 使用参数绑定，禁止拼接。
- 输出到 HTML 的用户数据必须转义。文件上传限制大小和类型。
- Cookie 会话要防 CSRF。对外重定向的目标地址走白名单。
- 短信、邮件、支付、下单等平台资源要防重放。
- 密码、密钥不进仓库；配置中的密码用环境变量，生产密钥加密或由环境注入。

## 数据库与接口

数据库条文以 `.ai/rules/30-database.md` 为准，其中已吸收黄山版里适用于本基线的强制项（软删除、禁用外键和存储过程、唯一列建唯一索引、不用 `SELECT *`、三表以上不 join、分页总数为 0 不再查当前页、布尔列与小数类型）。

接口另外遵守：

- 协议、路径、方法、请求体、状态码、响应体以契约为准。
- JSON 字段 lowerCamelCase。列表为空返回 `[]`，不返回 null。
- 页码小于 1 时按第 1 页处理（`Pagination` 已实现）。单页上限 200。
- URL 查询串不超过 2048 字节；请求体设置大小上限。
- 超过 JavaScript 安全整数范围的整数用字符串，主键已经这样做。

## 工程与设计

- 依赖使用语义化版本。线上不依赖 SNAPSHOT（安全补丁除外）。同一依赖在全反应器里只有一个版本，由父 POM 的 `dependencyManagement` 管理。
- 新增或升级依赖时看清传递依赖有没有被抬高或换掉；需要引入清单以外的库时停下来，走 ADR。
- 二方库的接口返回值不用枚举类型或包含枚举的 POJO 作为序列化合同；跨进程用契约里的字符串枚举。
- 远程调用必须设置连接和读取超时。
- 超过 3 个状态的对象在 `design.md` 里写清状态和触发条件。调用链上超过 3 个对象、或对象协作复杂时，用时序或活动说明把主路径写清楚。
- 标出弱依赖，并写明失败时如何降级，保证核心路径可用。

## 推荐项（默认遵守）

- 名字用完整单词。表示类型的词放在末尾，如 `startTime`、`nameList`。使用了某种模式时，类名里出现该模式。
- 接口方法不加多余的 `public`。固定取值范围用枚举，不要用无约束的字符串或整数。
- 单个方法尽量不超过 80 行。不同业务块之间空一行，不要为了对齐等号补空格。
- 局部变量优先基本类型。类内顺序：公有和保护方法、私有方法、getter / setter。重载方法放在一起。setter 不写业务。
- 访问范围从紧：工具类构造方法私有；只在内部用的成员私有。
- 循环拼接字符串用 `StringBuilder`。集合初始化时给出容量。遍历 `Map` 用 `entrySet` 或 `forEach`。
- `HashMap` 的 key 和 value 都可以是 null；`ConcurrentHashMap` 都不可以。
- 共享的 `Random` 在高并发下会抢种子，需要时各线程自建，或者改用 `ThreadLocalRandom`（非安全场景）。
- 获取单个对象用 `get`，多个用 `list`，计数用 `count`，删除用 `delete` 或 `remove`，修改用 `update`。与契约里的 `operationId` 冲突时以契约为准。
