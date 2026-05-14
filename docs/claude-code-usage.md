# Claude Code Usage Guide

> 地球 Online 当前优先按 Claude Code 原生 Skill 使用和验证。jiuwenclaw / openclaw adapter 保留为后续宿主集成方向。

## 使用目标

在 Claude Code 对话中直接体验完整闭环：

```text
早安 / 今日副本
  ↓
记录今天要做的事
  ↓
完成任务并获得积分
  ↓
查看剩余任务
  ↓
晚间结算
  ↓
查看 / 兑换奖励
```

## 运行态数据

默认运行态目录：

```text
runtime/data/
```

首次调用工具时，会从：

```text
examples/seed-data/
```

复制初始数据。

临时测试时可使用环境变量：

```bash
EARTH_ONLINE_DATA_ROOT=/tmp/earth-online-data PYTHONIOENCODING=utf-8 python scripts/smoke_test.py
```

## 核心对话与工具映射

### 首次初始化 / 玩家档案

用户：

```text
帮我初始化地球 Online
```

推荐流程：

```bash
python scripts/tools/init_skill_profile.py '{"render":true}'
```

如果返回 `next_action=ask_required_fields`，按 `recommended_questions` 询问用户。用户明确确认必填字段后：

```bash
python scripts/tools/apply_init_config.py '{"confirmed_by_user":true,"confirmed_fields":["name","timezone"],"required_fields":["name","timezone"],"name":"DemoUser","timezone":"Asia/Shanghai","render":true}'
```

不要用默认值跳过确认。

### 早安 / 今日副本

用户：

```text
早安
```

推荐工具流程：

```bash
python scripts/tools/record_morning_checkin.py '{"render": true}'
python scripts/tools/get_morning_brief.py '{"render": true}'
```

Claude Code 回复时，合并两个工具返回的 `message`。

### 创建任务

用户：

```text
我今天要整理项目计划
```

推荐调用：

```bash
python scripts/tools/create_task.py '{"name":"整理项目计划","type":"main","render":true}'
```

习惯型支线：

```bash
python scripts/tools/create_task.py '{"name":"阅读30分钟","type":"side","recurrence":"daily","render":true}'
```

### 完成任务

用户：

```text
项目计划整理完了
```

推荐调用：

```bash
python scripts/tools/complete_task.py '{"task_query":"项目计划","render":true}'
```

如果返回 `needs_confirmation`，先让用户确认具体任务。

### 查看当前任务

用户：

```text
我现在还有什么任务
```

推荐调用：

```bash
python scripts/tools/list_active_tasks.py '{"render":true}'
```

### 修改任务

用户：

```text
把项目计划改成明天截止
```

推荐调用：

```bash
python scripts/tools/update_task.py '{"task_query":"项目计划","deadline":"2026-03-26","render":true}'
```

### 取消任务

用户：

```text
取消阅读30分钟这个任务
```

推荐调用：

```bash
python scripts/tools/cancel_task.py '{"task_query":"阅读30分钟","render":true}'
```

### 每日结算

用户：

```text
今天结算一下
```

推荐调用：

```bash
python scripts/tools/get_daily_settlement.py '{"render":true}'
```

### 奖励列表

用户：

```text
有什么奖励可以兑换
```

推荐调用：

```bash
python scripts/tools/list_rewards.py '{"render":true}'
```

### 奖励兑换

用户：

```text
我想兑换周末看电影
```

先预览：

```bash
python scripts/tools/redeem_reward.py '{"reward_query":"看电影","render":true}'
```

如果用户确认：

```bash
python scripts/tools/redeem_reward.py '{"reward_query":"看电影","confirm":true,"render":true}'
```

## Claude Code 回复规则

- 工具返回 `message` 时，优先使用 `message` 回复用户。
- 工具返回 `success=false` 且带 `message` 时，把它当成可读失败说明。
- 工具返回 `needs_confirmation` 时，不要猜，列出候选让用户确认。
- 奖励兑换必须二次确认，除非用户已经明确说“确认兑换”。
- 不直接手改 `runtime/data/*.json`，除非用户明确要求修复数据。

## 验证命令

核心闭环：

```bash
PYTHONIOENCODING=utf-8 python scripts/smoke_test.py
```

真实对话边界：

```bash
PYTHONIOENCODING=utf-8 python scripts/dialogue_edge_smoke_test.py
PYTHONIOENCODING=utf-8 python scripts/onboarding_smoke_test.py
```

CLI 工具入口：

```bash
PYTHONIOENCODING=utf-8 python scripts/cli_smoke_test.py
```

adapter 原型：

```bash
PYTHONIOENCODING=utf-8 python scripts/adapter_smoke_test.py
```

Windows shell 下如果中文乱码，优先使用 `PYTHONIOENCODING=utf-8`。

## 当前边界

当前优先验证 Claude Code 对话体验。

暂不优先扩展：

- jiuwenclaw 深度适配
- openclaw 深度适配
- 常驻调度器
- Web dashboard

这些等 Claude Code Skill 链路稳定后再推进。
