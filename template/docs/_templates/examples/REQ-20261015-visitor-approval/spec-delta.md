# 规格增量：REQ-20261015-visitor-approval

## 能力：`visitor-appointment`

### 新增的业务规则

- **BR-visitor-appointment-09**：预约"需审批"楼层时，预约状态为"待审批"，不生成通行码。
- **BR-visitor-appointment-10**：只有被访人本人可以审批；审批结果为通过或驳回，驳回必须填写原因（1～200 个字符）。
- **BR-visitor-appointment-11**：审批通过后生成通行码并短信通知访客；驳回后短信通知访客驳回原因。
- **BR-visitor-appointment-12**：本规则上线前已创建的预约视为无需审批。

### 修改的业务规则

- **BR-visitor-appointment-03**（原：预约成功即生成通行码）改为：预约成功后，无需审批的预约立即生成通行码；需审批的预约按 BR-visitor-appointment-11 处理。

### 新增或修改的验收标准

#### AC-visitor-appointment-07：涉密楼层预约进入待审批

- 关联规则：BR-visitor-appointment-09
- 前提：12 层设置为"需审批"
- 操作：访客预约拜访 12 层员工
- 结果：预约状态为"待审批"，没有通行码

#### AC-visitor-appointment-08：被访人审批通过后生成通行码

- 关联规则：BR-visitor-appointment-11
- 前提：存在待审批的预约
- 操作：被访人点击"通过"
- 结果：预约状态为"已通过"，生成通行码，访客收到短信

#### AC-visitor-appointment-09：驳回必须填写原因

- 关联规则：BR-visitor-appointment-10
- 前提：存在待审批的预约
- 操作：被访人不填原因点击"驳回"
- 结果：提示"请填写驳回原因"，预约状态不变

#### AC-visitor-appointment-10：非被访人不能审批

- 关联规则：BR-visitor-appointment-10
- 前提：存在被访人为 A 的待审批预约
- 操作：员工 B 调用审批接口
- 结果：返回 403，错误码 A0403，预约状态不变

#### AC-visitor-appointment-11：存量预约照常放行

- 关联规则：BR-visitor-appointment-12
- 前提：上线前已创建的 12 层预约（已有通行码）
- 操作：上线后访客到访核销通行码
- 结果：核销成功
