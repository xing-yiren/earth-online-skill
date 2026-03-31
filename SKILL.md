---
name: earth-online-skill
description: >
  将用户的日常任务、晨间签到、积分、成就和奖励组织成“地球Online闯关”式体验的 Skill。
  适用于 claw 类宿主平台中的生活游戏化、任务推进、每日结算、奖励兑换等场景。
  当用户表达“早安/开启今天/今日副本/今天要做什么/我完成了某事/今天结算/兑换奖励”等意图时使用。
---

# 地球Online Skill

地球Online 是一个运行在宿主 Agent 之上的游戏化生活 Skill。

它不负责替代宿主的 memory、session 或意图识别，而是基于宿主提供的上下文，将用户的日常推进映射成：

- 今日副本
- 主线 / 支线任务
- 积分与等级
- 成就与 streak
- 每日结算
- 奖励兑换

## 何时使用

当用户出现以下意图时，应考虑触发本 Skill：

- 早安、开启今天、今日副本、今天有什么任务
- 我今天要做某事、我想坚持某个习惯
- 我完成了某事、我打卡了、今天做完了
- 今天结算、今天做了什么、每日结算
- 有什么奖励、我想兑换某个奖励

## 宿主职责

宿主平台负责：

- 提供用户身份与 profile
- 提供 memory、recent messages、session
- 做自然语言理解与意图识别
- 调用 Skill 工具

本 Skill 负责：

- 维护任务、积分、成就、奖励等私有状态
- 输出游戏化反馈与结算结果
- 在 runtime 中维护用户自己的 Skill 状态

## 输入前提

本 Skill 优先依赖宿主传入的统一 `host_context`。

最小输入应至少包含：

```json
{
  "host": { "platform": "some-claw-host" },
  "user": { "id": "demo-user" },
  "session": { "current_date": "2026-03-25" }
}
```

如果宿主提供了更多上下文，Skill 可以进一步使用：

- `user.name`
- `user.timezone`
- `intent.name`
- `context.recent_messages`
- `context.memory_facts`
- `context.preferences`
- `context.uncertainties`

## 运行态约定

- 仓库内示例数据位于 `examples/seed-data/`
- 真实运行态位于 `runtime/data/`
- 首次运行时，runtime 会从 seed data 初始化
- onboarding / init 工具负责把宿主上下文转成用户自己的运行态配置

## 核心行为

### 1. 晨间签到

当用户在晨间窗口内触发“早安 / 开启今天 / 今日副本”等行为时：

- 记录晨间签到
- 判断是否满足早起窗口
- 更新 `early_bird_streak`
- 检查相关成就

注意：
V1 中的“早起”表示**在晨间签到窗口内完成有效签到**，不等于真实生理起床时间。

### 2. 创建任务

当宿主识别到用户表达未来意图时：

- 创建主线或支线任务
- 默认主线偏 `once`
- 默认支线偏 `daily`

### 3. 完成任务

当宿主识别到用户表达“已完成”时：

- 更新任务状态
- 增加积分
- 更新成就统计
- 补发新解锁成就奖励积分

### 4. 每日结算

当用户请求结算或宿主定时触发时：

- 汇总今日完成情况
- 汇总今日积分变化
- 展示今日新成就
- 返回明日仍待推进的任务

### 5. 奖励兑换

当用户请求查看或兑换奖励时：

- 列出当前可用奖励
- 在兑换前要求确认
- 扣积分并记录兑换历史

## 工具入口

当前核心工具包括：

- `init_skill_profile`
- `apply_init_config`
- `record_morning_checkin`
- `create_task`
- `complete_task`
- `get_morning_brief`
- `get_daily_settlement`
- `list_rewards`
- `redeem_reward`

## 使用原则

- 优先依赖宿主的语义理解，不在 Skill 内做强关键词硬解析
- 让详细协议与数据结构留在 `docs/specs/`
- 让宿主差异留在 adapter 层
- 让 `SKILL.md` 保持短、清晰、可触发

## 参考文档

需要详细信息时，再读取：

- `docs/product/v1-prd.md`
- `docs/specs/host-context-spec.md`
- `docs/specs/host-adapter-spec.md`
- `docs/specs/data-and-tools-spec.md`
- `docs/roadmap/init-and-adapter-plan.md`
