# Jiuwenclaw Test Cases

> 面向 jiuwenclaw 正式接入前后的测试清单，覆盖初始化、adapter、任务、晨报、结算与奖励主场景。

---

## 1. 初始化场景

### Case 1: 首次接入，宿主信息完整

前提：
- adapter 可读取到用户 id、name、timezone

预期：
- `init_skill_profile` 返回 `initialized = false`
- `required_fields = []`
- `next_action = ready`

### Case 2: 首次接入，宿主缺少用户称呼

前提：
- adapter 输出 `user_name_missing`

预期：
- `required_fields` 包含 `name`
- `next_action = ask_required_fields`

### Case 3: 首次接入，宿主缺少时区

前提：
- adapter 输出 `timezone_missing`

预期：
- `required_fields` 包含 `timezone`
- `next_action = ask_required_fields`

### Case 4: 用户完成初始化

步骤：
- 调 `apply_init_config`

预期：
- `runtime/data/USER.md` 写入成功
- `.earth_online_init.json` 写入成功
- 再次调用 `init_skill_profile` 返回 `initialized = true`

---

## 2. Adapter 场景

### Case 5: 构造标准 host_context

步骤：
- 调 `JiuwenclawAdapter.build_host_context()`

预期：
- 返回包含 `host/user/session/intent/context/runtime`
- `host.platform = jiuwenclaw`
- `session.current_date` 存在

### Case 6: 用户名与 Agent 名冲突

前提：
- `USER.md` 备注中包含 Agent 别名信息

预期：
- adapter 输出 `context.uncertainties`
- 不应直接把 Agent 名强行当成用户名

### Case 7: recent messages 清洗

前提：
- `messages.json` 包含低价值消息，如 `okie`、`stop`

预期：
- 这些消息不会全部进入 `recent_messages`

---

## 3. 晨间链场景

### Case 8: 晨间签到成功

步骤：
- 在晨间窗口内调用 `record_morning_checkin`

预期：
- `is_early_bird = true`
- `early_bird_streak` 增加
- 可能触发早起类成就

### Case 9: 同日重复签到

预期：
- `already_recorded = true`
- 不重复增加 streak

### Case 10: 超过晨间窗口签到

预期：
- `is_early_bird = false`
- 不增加 `early_bird_streak`

---

## 4. 任务链场景

### Case 11: 创建主线任务

步骤：
- 调 `create_task`

预期：
- 创建成功
- `recurrence = once`

### Case 12: 创建支线任务

预期：
- 创建成功
- `recurrence = daily`

### Case 13: 重复创建 daily

预期：
- 返回 `duplicate_task`

### Case 14: 完成主线任务

预期：
- 任务状态更新
- 增加任务积分
- 更新成就统计

### Case 15: 重复完成 once

预期：
- 返回 `task_already_completed`

### Case 16: 同日重复完成 daily

预期：
- 返回 `task_already_completed_today`

---

## 5. 晨报与结算场景

### Case 17: 获取晨报

预期：
- 返回玩家名
- 返回 active 主线 / 支线
- 返回当前积分与等级

### Case 18: 获取每日结算

预期：
- 返回今日完成数
- 返回今日积分变化
- 返回 pending tasks
- 返回今日新成就

---

## 6. 奖励场景

### Case 19: 查看奖励列表

预期：
- 返回启用状态的奖励目录

### Case 20: 兑换前确认

预期：
- 返回 `confirmation_required`

### Case 21: 积分足够时兑换成功

预期：
- 扣积分
- 写 `redemption_history`

### Case 22: 积分不足时兑换失败

预期：
- 返回 `insufficient_points`

---

## 7. 推荐测试顺序

建议正式对接 jiuwenclaw 时按这个顺序验证：

1. Case 5
2. Case 1-4
3. Case 8-10
4. Case 11-16
5. Case 17-18
6. Case 19-22
