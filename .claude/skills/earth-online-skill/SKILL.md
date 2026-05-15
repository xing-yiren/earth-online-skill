---
name: earth-online-skill
description: >
  把日常任务、晨间签到、积分、成就和奖励组织成“地球Online闯关”式体验。
  当用户说“早安”“今天有什么任务”“我今天要做某事”“我完成了某事”“今天结算”“我想兑换奖励”时使用。
---

# 地球Online Skill

地球Online 是一个运行在 Claude Code 中的游戏化生活 skill。

## 何时使用

当用户表达以下意图时，触发本 skill：

- 早安、开启今天、今日副本、今天有什么任务
- 我今天要做某事、以后每天做某事、我想坚持某个习惯
- 我完成了某事、我打卡了、今天做完了
- 我还有什么任务、帮我改一下任务、取消这个任务
- 今天结算、今天做了什么
- 有什么奖励、我想兑换某个奖励
- 帮我初始化地球 Online

## 工作方式

优先调用 `scripts/tools/*.py`，并传入 `render=true`。

如果工具结果包含 `message`，优先直接使用 `message` 回复用户。

如果工具返回以下状态，不要猜测，先向用户确认：

- `needs_confirmation`
- `confirmation_required`
- `task_not_found`

## 常用工具路线

### 首次初始化

1. 调用 `init_skill_profile`。
2. 如果返回 `next_action=ask_required_fields`，按 `recommended_questions` 询问用户。
3. 用户明确确认后，再调用 `apply_init_config`。
4. 不要用默认值跳过确认。

### 早安 / 今日副本

1. 调用 `record_morning_checkin`
2. 调用 `get_morning_brief`
3. 合并两条 `message`

### 创建任务

- 主线通常用 `create_task(type=main, recurrence=once)`
- 习惯型任务通常用 `create_task(type=side, recurrence=daily)`

### 完成任务

- 用 `complete_task`
- 没有 task id 时可传 `task_query`
- 如果多候选，必须让用户确认

### 查看 / 修改 / 取消任务

- `list_active_tasks`
- `update_task`
- `cancel_task`

### 每日结算

- `get_daily_settlement`

### 奖励

- 查看奖励：`list_rewards`
- 兑换奖励：`redeem_reward`
- 奖励兑换要二次确认，除非用户已经明确说“确认兑换”

## 规则

- 不直接编辑 `runtime/data/*.json`，正常状态变更必须走工具入口。
- `core` 负责事实和状态，`renderer` 负责自然语言表达。
- 当前优先验证 Claude Code 对话体验；jiuwenclaw / openclaw adapter 是后续集成方向。

## 参考文档

需要细节时再读：

- `docs/claude-code-usage.md`
- `docs/testing/claude-code-dialogue-test-prompts.md`
- `docs/specs/data-and-tools-spec.md`
- `docs/specs/scheduler-integration-spec.md`
