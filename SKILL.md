---
name: earth-online-skill
description: >
  将用户的日常任务、晨间签到、积分、成就和奖励组织成“地球Online闯关”式体验的 Claude Code Skill。
  当用户表达“早安/开启今天/今日副本/今天要做什么/我完成了某事/今天结算/兑换奖励”等意图时使用。
---

# 地球Online Skill

地球Online 是一个优先运行在 Claude Code 中的游戏化生活 Skill。

它把用户的日常推进映射成：

- 今日副本
- 主线 / 支线任务
- 积分与等级
- 成就与 streak
- 每日结算
- 奖励兑换

当前主路径是：

```text
Claude Code 对话
  ↓
识别用户意图
  ↓
调用 scripts/tools/*
  ↓
必要时使用 scripts/renderers/* 生成自然语言回复
  ↓
把游戏化反馈返回给用户
```

jiuwenclaw / openclaw 等 adapter 是后续宿主集成方向，不是当前核心依赖。

## 何时使用

当用户出现以下意图时，应考虑触发本 Skill：

- 早安、开启今天、今日副本、今天有什么任务
- 我今天要做某事、我想坚持某个习惯、以后每天做某事
- 我完成了某事、我打卡了、今天做完了
- 现在还有什么任务、今天还有什么
- 改一下任务、取消某个任务、刚才记错了
- 今天结算、今天做了什么、每日结算
- 有什么奖励、我想兑换某个奖励

## Claude Code 使用规则

在 Claude Code 中使用时：

1. 由 Claude 根据用户自然语言判断意图。
2. 调用对应 `scripts/tools/*.py` 工具，优先传入 `render=true`。
3. 如果工具结果包含 `message`，优先直接把 `message` 作为用户回复主体。
4. 如果工具返回 `needs_confirmation`、`confirmation_required`、`task_not_found` 等状态，向用户确认，不要自行猜测。
5. 不要直接编辑 `runtime/data/*.json`，除非是在修复数据问题；正常状态变更必须走工具入口。
6. 早播报和晚结算的定时触发由 Claude Code 外层调度或用户主动触发，Skill 本体不自建常驻调度器。

## 常见意图与工具映射

### 首次初始化 / 玩家档案

首次使用或用户要求配置地球 Online 时：

1. 调用 `init_skill_profile`，传入 `render=true`。
2. 如果返回 `ask_required_fields`，按 `recommended_questions` 询问用户。
3. 用户明确确认必填字段后，调用 `apply_init_config`，传入 `confirmed_by_user=true`、`confirmed_fields=[...]` 和 `render=true`。
4. 建档完成后（无论新建档还是已初始化），**必须接着推进候选任务导入**（见下一节），不要停在建档消息上。
5. 如果用户之前已经初始化过，简要确认当前称呼和时区即可，然后直接推进候选导入。

### 候选任务导入（建档后必须执行）

建档完成后，**不要只回复建档 message 就停下**。必须主动推进：

1. 从当前对话上下文中整理 `raw_candidates`（字符串或带字段的 dict），调用 `suggest_onboarding_imports`，传入 `render=true`。
2. 工具只生成候选，不会写入任务；展示后让用户确认要导入哪些。
3. 用户确认后，调用 `apply_onboarding_imports`，把用户选中的候选放在 `selected_candidates`，传入 `render=true`。
4. 如果当前上下文确实提取不出任何候选，不要空调 `suggest_onboarding_imports`。直接问用户想追踪什么任务，然后用 `create_task` 逐个创建。
5. 如果用户说"都不要"或"跳过"，尊重用户选择，直接进入今日副本。
6. 整个过程不要跳过用户确认。

### 早安 / 开启今日副本

推荐流程：

1. 调用 `record_morning_checkin`，传入 `render=true`。
2. 调用 `get_morning_brief`，传入 `render=true`。
3. 合并两个工具的 `message` 回复用户。

### 创建任务

用户表达未来意图时调用 `create_task`：

- 主线任务通常是 `type=main`、`recurrence=once`
- 支线习惯通常是 `type=side`、`recurrence=daily`
- 如用户未指定积分，可使用工具默认积分
- 传入 `render=true` 获取自然语言反馈

### 完成任务

用户表达已完成时调用 `complete_task`：

- 优先用明确任务 id
- 没有 id 时用 `task_query`
- 如果返回多候选，必须让用户确认
- 成功后工具会联动任务状态、积分、成就奖励

### 查看任务

用户询问“我还有什么任务”时调用 `list_active_tasks`，传入 `render=true`。

### 修改 / 取消任务

用户想改名、改截止时间、改积分、改任务类型时调用 `update_task`。

用户想删除、取消、不做某任务时调用 `cancel_task`。

### 每日结算

用户请求“今天结算 / 今天做了什么”时调用 `get_daily_settlement`，传入 `render=true`。

### 奖励兑换

用户查看奖励时调用 `list_rewards`，传入 `render=true`。

用户请求兑换时调用 `redeem_reward`：

- 第一次通常传 `confirm=false` 或不传 confirm
- 如果返回 `confirmation_required`，向用户确认
- 用户明确确认后再传 `confirm=true`

## 运行态约定

- 仓库内示例数据位于 `examples/seed-data/`
- 真实运行态位于 `runtime/data/`
- 首次运行时，runtime 会从 seed data 初始化
- 可用 `EARTH_ONLINE_DATA_ROOT` 指向临时数据目录进行测试
- `USER.md` 保存用户配置，不保存任务、积分、成就状态

## Onboarding 约束

如果 `init_skill_profile` 返回：

- `initialized = false`
- `next_action = ask_required_fields`

那么必须：

1. 根据 `required_fields` 继续向用户提问
2. 不得直接跳过到正常玩法
3. 不得直接以默认值调用 `apply_init_config`

调用 `apply_init_config` 时，应显式传入：

- `confirmed_by_user = true`
- `confirmed_fields = [...]`

否则初始化工具应拒绝执行。

## 宿主 adapter 定位

跨宿主接入时，adapter 只负责把宿主私有结构转换成标准 `host_context`。

推荐边界：

```text
宿主平台 / adapter
  ↓
统一 host_context
  ↓
earth-online-skill tools
  ↓
renderers
  ↓
宿主投递消息
```

不要让 core service 直接依赖 jiuwenclaw、openclaw 等宿主私有 memory 或 session 文件。

## 使用原则

- Claude Code 路径优先，先验证真实对话体验
- core service 负责事实和状态，renderer 负责表达和体验
- 优先使用结构化工具，不直接手写 JSON 状态
- 让详细协议与数据结构留在 `docs/specs/`
- 让宿主差异留在 adapter 层
- 让 `SKILL.md` 保持短、清晰、可触发

## 参考文档

需要详细信息时，再读取：

- `docs/claude-code-usage.md`
- `docs/testing/claude-code-dialogue-test-prompts.md`
- `docs/product/v1-prd.md`
- `docs/specs/data-and-tools-spec.md`
- `docs/specs/scheduler-integration-spec.md`
- `docs/specs/host-context-spec.md`
- `docs/specs/host-adapter-spec.md`
