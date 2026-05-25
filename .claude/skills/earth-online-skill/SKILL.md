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
- `/earth-online-skill` 或 `地球online` 后跟子命令（见下方命令行模式）

## 命令行模式

用户可以用 `/earth-online-skill <command>` 或 `地球online <command>` 直接操作：

| 命令 | 映射工具 |
|------|---------|
| `init` | 启动建档流程。如果已初始化，询问"重新建档"还是"查看当前档案" |
| `checkin` / `早安` / `签到` | `record_morning_checkin` + `get_morning_brief` |
| `tasks` / `任务` | `list_active_tasks` |
| `create` / `创建` | 询问任务名称和类型后调用 `create_task` |
| `settle` / `结算` | `get_daily_settlement` |
| `rewards` / `奖励` | `list_rewards` |
| `scan` / `扫描` | 跨会话任务扫描（见下方） |

如果子命令不在上述列表中，按自然语言意图正常处理。

## 跨会话任务扫描

用户可以用 `scan` 命令或说"扫描所有会话"来触发。

**关键约束：必须先获得用户明确许可才能扫描。** 会话记录是敏感数据。

流程：

1. 调用 `scan_sessions render=true`（不带 `confirmed_by_user`）。
2. 工具会返回 `confirmation_required`，展示确认提示。
3. 用户明确说"确认"后，调用 `scan_sessions`，传入 `confirmed_by_user=true` 和 `render=true`。
4. 工具返回候选列表后，展示给用户确认。
5. 用户选好后，用 `apply_onboarding_imports` 导入。
6. 整个过程不要跳过任何确认步骤。

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

**游戏化建档流程。** 这是玩家首次进入地球 Online 的角色创建环节，请用游戏系统风格呈现。

1. 调用 `init_skill_profile render=true`。
2. 如果返回 `next_action=ask_required_fields`：
   - 先**自动检测玩家信息**：从当前会话上下文中尝试推断玩家称呼（如系统用户名、Git 用户名、之前的对话中出现的名字等），将检测结果作为"系统检测默认值"展示。
   - 按工具返回的 `message` 展示角色创建表单（已含游戏风格边框和"系统自检中"等过渡语言）。
   - 逐项确认，不要直接用默认值跳过。
   - 如果用户一次性回复了多项信息（如"叫我小明，时区 Asia/Shanghai"），解析并全部填入。
3. 用户确认必填字段后，调用 `apply_init_config`，显式传入 `confirmed_by_user=true` 和 `confirmed_fields`。
4. 建档完成后（无论 `initialized=true` 还是 `apply_init_config` 成功），**必须接着推进候选任务导入**（见下一节），不要停在建档消息上。过渡时可以加入"系统就绪，正在加载任务模块..."等游戏化衔接语。
5. 如果用户之前已经初始化过，但**用户明确输入了 `init` 命令**：说明用户想要重新建档。先展示当前档案，然后问"要重新建档吗？"——如果用户确认，调用 `apply_init_config` 传入新值覆盖；如果用户拒绝，直接推进候选导入。如果玩家称号仍为默认值"玩家"，**必须先建议用户更新称号**。

### 候选任务导入（建档后必须执行）

建档完成后，**不要只回复建档 message 就停下**。你必须主动推进：

1. 从当前对话上下文中整理 `raw_candidates`（字符串列表或带字段的 dict，例如用户提到的待办事项、计划、习惯等）。
2. **如果有可提取的候选**：调用 `suggest_onboarding_imports`，把 `raw_candidates` 作为 JSON 数组传入。展示候选列表，让用户确认要导入哪些。用户选好后，把对应条目放入 `selected_candidates`，调用 `apply_onboarding_imports render=true`。
3. **如果当前上下文候选较少或为空**：**必须主动询问用户**："要不要我扫描你所有项目的 Claude Code 会话记录，从中提取可能遗漏的任务？" —— 如果用户同意，走跨会话任务扫描流程（见下方）；如果用户拒绝，再问用户今天想追踪什么任务。
4. 如果用户说"都不要"或"跳过"，尊重用户选择，直接进入今日副本。
5. 整个过程不要跳过用户确认。

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
