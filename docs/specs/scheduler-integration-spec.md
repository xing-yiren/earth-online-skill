# Scheduler Integration Spec

> 地球 Online Skill 的早播报与晚结算由宿主平台定时触发，Skill 本体只提供可调用能力，不自建调度器。

## 目标

明确宿主如何在每天固定时间调用地球 Online 工具，避免把 cron、后台进程、平台 hook 等宿主能力耦合进核心业务逻辑。

## 边界

Skill 本体负责：

- 记录晨间签到
- 返回今日早播报结构化数据
- 返回每日结算结构化数据
- 根据结构化结果生成自然语言回复

宿主平台负责：

- 保存用户调度偏好
- 定时触发工具调用
- 提供 `host_context`
- 决定消息投递渠道
- 处理失败重试与通知权限

## 推荐调度点

默认用户配置来自 `USER.md`：

```md
- **morning_broadcast**: 07:00
- **evening_settlement**: 22:00
- **broadcast_channel**: webchat
```

宿主可以允许用户覆盖这些配置。

## 早播报流程

建议在 `morning_broadcast` 时间附近触发：

1. 宿主构造 `host_context`
2. 调用 `record_morning_checkin`
3. 调用 `get_morning_brief`
4. 使用 `render_morning_checkin` 和 `render_morning_brief` 生成回复
5. 通过用户配置的渠道投递

示例输入：

```json
{
  "date": "2026-03-25",
  "current_time": "2026-03-25T07:05:00+08:00",
  "host_context": {
    "host": { "platform": "jiuwenclaw" },
    "user": { "id": "demo-user", "name": "DemoUser", "timezone": "Asia/Shanghai" },
    "session": { "current_date": "2026-03-25" },
    "runtime": { "trigger": "schedule", "locale": "zh-CN" }
  }
}
```

## 晚结算流程

建议在 `evening_settlement` 时间附近触发：

1. 宿主构造 `host_context`
2. 调用 `get_daily_settlement`
3. 使用 `render_daily_settlement` 生成回复
4. 投递给用户

示例输入：

```json
{
  "date": "2026-03-25",
  "host_context": {
    "host": { "platform": "jiuwenclaw" },
    "user": { "id": "demo-user", "name": "DemoUser", "timezone": "Asia/Shanghai" },
    "session": { "current_date": "2026-03-25" },
    "runtime": { "trigger": "schedule", "locale": "zh-CN" }
  }
}
```

## 幂等要求

宿主重复触发同一天早播报时：

- `record_morning_checkin` 应返回 `already_recorded = true`
- 宿主可以选择仍发送播报，也可以只发送简短提醒

宿主重复触发同一天晚结算时：

- `get_daily_settlement` 是只读聚合，可重复调用
- 宿主可根据自身消息记录避免重复推送

## 失败处理

推荐策略：

- 工具调用失败：宿主记录失败原因，不应修改 Skill 状态
- 消息投递失败：宿主负责重试，Skill 不感知渠道失败
- `host_context` 缺字段：宿主优先补齐；Skill 可使用本地默认值降级

## Adapter 定位

Adapter 只负责把宿主私有结构转换为标准 `host_context`。

不建议让 core service 直接读取宿主私有目录，例如：

- jiuwenclaw 的 `USER.md` / `MEMORY.md` / `messages.json`
- openclaw 的内部 session 或 memory 存储

推荐调用链：

```text
宿主定时器
  ↓
adapter 构造 host_context
  ↓
Skill tool
  ↓
renderer
  ↓
宿主消息投递
```
