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

调用工具时使用以下任一格式：

```bash
python scripts/tools/<tool>.py '{"render":true}'
python scripts/tools/<tool>.py render=true
```

优先用 JSON 参数；如果只传简单参数，`key=value` 也可用。

工具结果包含 `message` 时，只回复一次 `message` 的内容，不要重复改写、不要重复粘贴、不要同时输出 JSON。

如果工具返回以下状态，不要猜测，先向用户确认：

- `needs_confirmation`
- `confirmation_required`
- `task_not_found`

## 常用工具路线

### 首次初始化

1. 调用 `init_skill_profile render=true`。
2. 如果返回 `next_action=ask_required_fields`，只向用户提出需要确认的问题。
3. 如果返回 `initialized=true`，直接回复工具 `message`，不要重复输出。
4. 用户明确确认后，再调用 `apply_init_config`。
5. 不要用默认值跳过确认。

### 候选任务导入（可选）

建档完成后，如果用户想快速导入一批初始任务：

1. 由你从当前对话/记忆/计划中整理 `raw_candidates`（字符串或带字段的 dict）。
2. 调用 `suggest_onboarding_imports render=true`，它只生成候选，不写任务。
3. 把候选展示给用户，等待用户确认。
4. 用户选好后，把对应条目放入 `selected_candidates`，调用 `apply_onboarding_imports render=true`。
5. 不要跳过用户确认。

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

- 最终回复保持简短：除非用户要求解释，否则直接返回工具 `message`。
- 不直接编辑 `runtime/data/*.json`，正常状态变更必须走工具入口。
- `core` 负责事实和状态，`renderer` 负责自然语言表达。
- 当前优先验证 Claude Code 对话体验；jiuwenclaw / openclaw adapter 是后续集成方向。

## 参考文档

需要细节时再读：

- `docs/claude-code-usage.md`
- `docs/testing/claude-code-dialogue-test-prompts.md`
- `docs/specs/data-and-tools-spec.md`
- `docs/specs/scheduler-integration-spec.md`
