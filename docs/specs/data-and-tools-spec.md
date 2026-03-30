# 地球Online Skill - V1 数据结构与工具接口规范

> 本文档是 `../SKILL.md` 的实现侧补充，定义 V1 的标准数据结构、状态约定与工具输入输出格式。

---

## 1. 文档目的

本规范只解决两个问题：

1. V1 的数据应该如何组织
2. Agent 调用底层工具时，输入输出应该长什么样

同时，本规范假设地球Online是一个跨宿主平台 Skill。不同宿主平台应先把自身 memory、profile、recent context 统一整理为 `host_context`，再调用 Skill 工具。

目标是让 Skill 层、脚本层和后续实现都基于同一套约定，避免再次出现多份数据源、重复字段和状态不一致的问题。

---

## 2. 宿主接入模型

### 2.1 Host Adapter 概念

不同宿主平台的 memory 和 session 结构可能完全不同，例如：

- qclaw 可能基于 sqlite、workspace 和平台级目录
- jiuwenclaw 可能基于 `USER.md`、`MEMORY.md`、`messages.json`
- openclaw 也可能有自己的内部结构

因此，地球Online 不直接依赖宿主的私有文件格式，而是通过宿主适配层输出统一 `host_context`。

### 2.2 Host Context 最小结构

```json
{
  "host": {
    "platform": "qclaw"
  },
  "user": {
    "id": "demo-user"
  },
  "session": {
    "current_date": "2026-03-25"
  }
}
```

### 2.3 Host Context 推荐结构

```json
{
  "host": {
    "platform": "jiuwenclaw",
    "skill_runtime_version": "1.0"
  },
  "user": {
    "id": "demo-user",
    "name": "DemoUser",
    "timezone": "Asia/Shanghai"
  },
  "session": {
    "session_id": "sess_001",
    "current_date": "2026-03-25",
    "current_time": "07:10:00+08:00"
  },
  "intent": {
    "name": "complete_task",
    "confidence": 0.92
  },
  "context": {
    "recent_messages": [
      "我今天要完成项目报告",
      "报告我已经做完了"
    ],
    "memory_facts": [
      "本周要交项目报告",
      "最近在准备面试"
    ],
    "preferences": [
      "喜欢游戏化表达",
      "不喜欢太正式的语气"
    ]
  }
}
```

### 2.4 字段要求

#### 必需字段

- `host.platform`
- `user.id`
- `session.current_date`

#### 推荐字段

- `user.name`
- `user.timezone`
- `intent.name`
- `intent.confidence`
- `context.memory_facts`
- `context.preferences`
- `context.recent_messages`

#### 可选扩展字段

- `context.calendar_summary`
- `context.today_focus`
- `context.energy_state`
- `context.last_settlement_summary`

---

## 3. 数据目录约定

V1 必须只使用一个统一数据根目录。

建议约定：

```text
<DATA_ROOT>/
  USER.md
  tasks.json
  points.json
  achievements.json
  rewards.json
```

说明：

- 不要在不同脚本中使用不同的数据目录
- 不要同时维护仓库内示例数据和运行时真实数据两套来源
- 所有工具都必须从同一 `DATA_ROOT` 读写

---

## 4. 文件职责划分

### 3.1 USER.md

用途：
- 保存用户基础配置
- 保存展示风格和定时播报配置

建议字段：

```md
# USER.md

## 基本信息
- **name**: DemoUser
- **timezone**: Asia/Shanghai

## 播报设置
- **morning_broadcast**: 07:00
- **evening_settlement**: 22:00

## 晨间签到设置
- **morning_target_time**: 07:00
- **early_bird_grace_minutes**: 30

## 风格设置
- **style**: standard

## 偏好设置
- **track_habits**: true
```

说明：
- USER.md 不保存任务、积分、成就状态
- USER.md 只保存配置型信息

---

### 3.2 tasks.json

用途：
- 保存任务定义
- 保存任务当前状态
- 保存任务完成日志

标准结构：

```json
{
  "version": "1.0",
  "task_counter": 2,
  "tasks": [
    {
      "id": "task_0001",
      "name": "完成项目报告",
      "type": "main",
      "recurrence": "once",
      "status": "active",
      "points": 80,
      "deadline": "2026-03-25",
      "created_at": "2026-03-24T09:00:00+08:00",
      "updated_at": "2026-03-24T09:00:00+08:00",
      "completed_at": null,
      "last_completed_date": null,
      "source": "agent"
    },
    {
      "id": "task_0002",
      "name": "阅读30分钟",
      "type": "side",
      "recurrence": "daily",
      "status": "active",
      "points": 20,
      "deadline": null,
      "created_at": "2026-03-24T09:10:00+08:00",
      "updated_at": "2026-03-24T21:30:00+08:00",
      "completed_at": null,
      "last_completed_date": "2026-03-24",
      "source": "agent"
    }
  ],
  "completion_log": [
    {
      "task_id": "task_0002",
      "task_name": "阅读30分钟",
      "type": "side",
      "points": 20,
      "completion_kind": "daily",
      "completed_at": "2026-03-24T21:30:00+08:00",
      "completed_date": "2026-03-24"
    }
  ]
}
```

字段说明：

- `type`: `main` | `side`
- `recurrence`: `once` | `daily`
- `status`: `active` | `completed` | `cancelled`

规则说明：

#### 一次性任务（once）
- 创建后默认 `status = active`
- 完成后更新为 `completed`
- `completed_at` 写入完成时间

#### 每日任务（daily）
- 任务本体始终保持 `status = active`
- 每日是否完成，依赖：
  - `last_completed_date`
  - `completion_log`
- 不应把每日任务永久改成 `completed`

说明：
- V1 不再使用“主线/支线/长期”三组数组结构
- V1 统一改为 `tasks[]` 列表，靠字段区分类型

---

### 3.3 points.json

用途：
- 保存积分、等级与积分流水
- 作为积分系统唯一真相源

标准结构：

```json
{
  "version": "1.0",
  "available_points": 850,
  "lifetime_points": 1200,
  "spent_points": 350,
  "current_level": 2,
  "level_title": "资深玩家",
  "history": [
    {
      "id": "txn_0001",
      "type": "earn",
      "amount": 80,
      "source": "task_complete",
      "source_id": "task_0001",
      "reason": "完成主线任务：完成项目报告",
      "created_at": "2026-03-24T21:20:00+08:00"
    },
    {
      "id": "txn_0002",
      "type": "spend",
      "amount": 200,
      "source": "reward_redeem",
      "source_id": "reward_0001",
      "reason": "兑换奖励：周末看电影",
      "created_at": "2026-03-24T22:05:00+08:00"
    }
  ]
}
```

字段说明：

- `available_points`: 当前可消费积分
- `lifetime_points`: 累计获得积分
- `spent_points`: 累计消费积分
- `current_level`: 当前等级
- `level_title`: 当前称号

规则说明：
- 积分与等级只保存在 `points.json`
- 其他文件不得重复维护积分总数与等级字段

---

### 3.4 achievements.json

用途：
- 保存成就解锁记录
- 保存和成就判定相关的统计信息

标准结构：

```json
{
  "version": "1.0",
  "stats": {
    "survival_days": 42,
    "early_bird_streak": 7,
    "best_early_bird_streak": 14,
    "last_early_bird_date": "2026-03-24",
    "tasks_completed_total": 23,
    "last_active_date": "2026-03-24"
  },
  "unlocked": [
    {
      "id": "early_bird_7",
      "name": "早起战士",
      "icon": "sunrise-warrior",
      "reward_points": 50,
      "reason": "连续早起达到7天",
      "unlocked_at": "2026-03-24T07:00:00+08:00"
    }
  ]
}
```

字段说明：

- `stats.survival_days`: 累计活跃天数
- `stats.early_bird_streak`: 当前连续晨间签到成功天数
- `stats.best_early_bird_streak`: 历史最佳连续晨间签到成功天数
- `stats.last_early_bird_date`: 最近一次晨间签到成功日期
- `stats.tasks_completed_total`: 累计完成任务数
- `unlocked`: 已解锁成就列表

规则说明：
- `achievements.json` 不保存当前积分、总积分、等级
- 成就奖励积分发放后，实际积分变化必须写入 `points.json`

说明：
V1 中的 `early_bird_*` 成就基于“晨间签到窗口内成功签到”的记录计算，不直接等于真实起床时间。

---

### 3.5 rewards.json

用途：
- 保存奖励目录
- 保存奖励兑换历史

标准结构：

```json
{
  "version": "1.0",
  "rewards": [
    {
      "id": "reward_0001",
      "name": "周末看电影",
      "cost": 200,
      "category": "entertainment",
      "description": "周末允许自己看一场电影",
      "is_enabled": true,
      "created_at": "2026-03-24T09:00:00+08:00"
    },
    {
      "id": "reward_0002",
      "name": "吃一顿大餐",
      "cost": 300,
      "category": "food",
      "description": "允许自己吃一顿想吃的",
      "is_enabled": true,
      "created_at": "2026-03-24T09:10:00+08:00"
    }
  ],
  "redemption_history": [
    {
      "reward_id": "reward_0001",
      "reward_name": "周末看电影",
      "cost": 200,
      "redeemed_at": "2026-03-24T22:05:00+08:00",
      "points_after": 650
    }
  ]
}
```

规则说明：
- 奖励目录与兑换历史必须保存在同一文件中
- 不要在保存奖励时覆盖掉 `redemption_history`
- 奖励通常是“可重复兑换目录项”，不建议兑换一次后直接把奖励本体改成永久失效

---

## 5. 等级规则建议

建议等级表：

```json
[
  { "level": 1, "min_points": 0, "title": "新手玩家" },
  { "level": 2, "min_points": 500, "title": "资深玩家" },
  { "level": 3, "min_points": 1000, "title": "高级玩家" },
  { "level": 4, "min_points": 2000, "title": "精英玩家" },
  { "level": 5, "min_points": 4000, "title": "大师玩家" },
  { "level": 6, "min_points": 7000, "title": "传奇玩家" }
]
```

说明：
- 等级根据 `available_points` 或统一规则计算
- V1 推荐直接基于 `available_points` 计算，规则简单且用户容易理解

---

## 6. V1 成就池建议

```json
[
  { "id": "first_day", "type": "survival", "threshold": 1, "reward_points": 10 },
  { "id": "survivor_7", "type": "survival", "threshold": 7, "reward_points": 30 },
  { "id": "survivor_30", "type": "survival", "threshold": 30, "reward_points": 100 },
  { "id": "early_bird_3", "type": "early_bird", "threshold": 3, "reward_points": 30 },
  { "id": "early_bird_7", "type": "early_bird", "threshold": 7, "reward_points": 50 },
  { "id": "early_bird_30", "type": "early_bird", "threshold": 30, "reward_points": 200 },
  { "id": "task_master_10", "type": "task_total", "threshold": 10, "reward_points": 50 },
  { "id": "task_master_50", "type": "task_total", "threshold": 50, "reward_points": 200 }
]
```

---

## 7. 工具接口规范

以下工具名称是建议抽象。具体实现可以是脚本、函数或模块，但输入输出格式建议保持稳定。

---

### 7.1 `get_morning_brief`

用途：
- 获取今日开局信息

输入：

```json
{
  "user_id": "demo-user",
  "date": "2026-03-25",
  "host_context": {
    "host": { "platform": "qclaw" },
    "user": { "id": "demo-user", "name": "DemoUser" },
    "session": { "current_date": "2026-03-25" }
  }
}
```

输出：

```json
{
  "success": true,
  "player_name": "DemoUser",
  "date": "2026-03-25",
  "survival_days": 42,
  "early_bird_streak": 7,
  "main_tasks": [
    {
      "id": "task_0001",
      "name": "完成项目报告",
      "points": 80,
      "deadline": "2026-03-25"
    }
  ],
  "side_tasks": [
    {
      "id": "task_0002",
      "name": "阅读30分钟",
      "points": 20,
      "completed_today": false
    }
  ],
  "current_points": 850,
  "current_level": 2,
  "level_title": "资深玩家"
}
```

---

### 7.2 `create_task`

用途：
- 创建任务

输入：

```json
{
  "name": "完成项目报告",
  "type": "main",
  "recurrence": "once",
  "deadline": "2026-03-25",
  "points": 80,
  "source": "agent",
  "host_context": {
    "host": { "platform": "jiuwenclaw" },
    "user": { "id": "demo-user", "name": "DemoUser" },
    "session": { "current_date": "2026-03-25" },
    "intent": { "name": "create_task", "confidence": 0.93 },
    "context": {
      "memory_facts": ["本周需要交项目报告"]
    }
  }
}
```

输出：

```json
{
  "success": true,
  "task": {
    "id": "task_0003",
    "name": "完成项目报告",
    "type": "main",
    "recurrence": "once",
    "status": "active",
    "deadline": "2026-03-25",
    "points": 80
  }
}
```

失败输出：

```json
{
  "success": false,
  "error": "duplicate_task",
  "message": "已存在相似的进行中任务"
}
```

---

### 7.3 `complete_task`

用途：
- 完成任务，并联动积分、成就和日志

输入：

```json
{
  "task_query": "项目报告",
  "date": "2026-03-25",
  "host_context": {
    "host": { "platform": "qclaw" },
    "user": { "id": "demo-user" },
    "session": { "current_date": "2026-03-25" },
    "intent": { "name": "complete_task", "confidence": 0.92 }
  }
}
```

成功输出：

```json
{
  "success": true,
  "task": {
    "id": "task_0001",
    "name": "完成项目报告",
    "type": "main",
    "recurrence": "once"
  },
  "points_gained": 80,
  "current_points": 930,
  "level_title": "资深玩家",
  "unlocked_achievements": [
    {
      "id": "task_master_10",
      "name": "任务达人",
      "reward_points": 50
    }
  ]
}
```

多候选输出：

```json
{
  "success": false,
  "error": "needs_confirmation",
  "candidates": [
    { "id": "task_0001", "name": "完成项目报告" },
    { "id": "task_0004", "name": "完善项目报告" }
  ]
}
```

未找到输出：

```json
{
  "success": false,
  "error": "task_not_found",
  "message": "没有找到匹配的进行中任务"
}
```

---

### 7.4 `get_daily_settlement`

用途：
- 获取每日结算信息

输入：

```json
{
  "user_id": "demo-user",
  "date": "2026-03-25",
  "host_context": {
    "host": { "platform": "openclaw" },
    "user": { "id": "demo-user", "name": "DemoUser" },
    "session": { "current_date": "2026-03-25" }
  }
}
```

输出：

```json
{
  "success": true,
  "date": "2026-03-25",
  "main_completed": 1,
  "main_total": 2,
  "side_completed": 1,
  "side_total": 2,
  "points_earned_today": 120,
  "completed_tasks": [
    { "name": "面试准备", "type": "main", "points": 100 },
    { "name": "晨跑", "type": "side", "points": 20 }
  ],
  "pending_tasks": [
    { "name": "完成项目报告", "type": "main" },
    { "name": "阅读30分钟", "type": "side" }
  ],
  "new_achievements": [
    { "id": "early_bird_7", "name": "早起战士" }
  ],
  "current_points": 950,
  "current_level": 2,
  "level_title": "资深玩家",
  "points_to_next_level": 50
}
```

---

### 7.5 `list_rewards`

用途：
- 查看奖励目录

输入：

```json
{
  "enabled_only": true,
  "host_context": {
    "host": { "platform": "kimiclaw" },
    "user": { "id": "demo-user" },
    "session": { "current_date": "2026-03-25" }
  }
}
```

输出：

```json
{
  "success": true,
  "rewards": [
    {
      "id": "reward_0001",
      "name": "周末看电影",
      "cost": 200,
      "category": "entertainment",
      "description": "周末允许自己看一场电影"
    }
  ]
}
```

---

### 7.6 `redeem_reward`

用途：
- 兑换奖励

输入：

```json
{
  "reward_query": "看电影",
  "confirm": true,
  "host_context": {
    "host": { "platform": "jiuwenclaw" },
    "user": { "id": "demo-user" },
    "session": { "current_date": "2026-03-25" },
    "intent": { "name": "redeem_reward", "confidence": 0.96 }
  }
}
```

成功输出：

```json
{
  "success": true,
  "reward": {
    "id": "reward_0001",
    "name": "周末看电影",
    "cost": 200
  },
  "points_spent": 200,
  "current_points": 650
}
```

积分不足输出：

```json
{
  "success": false,
  "error": "insufficient_points",
  "required": 200,
  "current_points": 150
}
```

未确认输出：

```json
{
  "success": false,
  "error": "confirmation_required",
  "reward": {
    "id": "reward_0001",
    "name": "周末看电影",
    "cost": 200
  },
  "current_points": 850
}
```

---

## 8. 状态流转规则

### 7.1 创建任务

`create_task` 成功后：
- 写入 `tasks.json.tasks`
- 不改积分
- 不触发成就

### 7.2 完成任务

`complete_task` 成功后：
- 更新 `tasks.json`
- 写入 `completion_log`
- 写入 `points.json.history`
- 更新 `available_points` 和 `lifetime_points`
- 更新 `achievements.json.stats.tasks_completed_total`
- 执行成就检查
- 如有新成就，再追加成就奖励积分流水

### 7.3 兑换奖励

`redeem_reward` 成功后：
- 扣减 `points.json.available_points`
- 写入 `points.json.history`
- 写入 `rewards.json.redemption_history`
- 不修改奖励目录本体可用性（除非后续版本引入限购机制）

---

## 9. 实现建议

### 8.1 必须避免的实现问题

- 不同脚本使用不同数据根目录
- 积分与等级在多个文件重复维护
- 完成任务后只返回文案，不真正加分
- 成就奖励只写成就文件，不写积分流水
- 保存奖励目录时覆盖兑换历史
- 让 Skill 直接耦合宿主私有 memory 文件格式

### 9.3 宿主适配建议

建议后续实现中增加 `Host Adapter` 层：

- qclaw adapter
- jiuwenclaw adapter
- openclaw adapter adapter

各 adapter 负责把宿主的 profile、memory、recent messages 和 session 信息转换成统一 `host_context`，再调用地球Online Skill。

### 8.2 V1 最小实现顺序

1. 统一数据目录
2. 实现 `create_task`
3. 实现 `complete_task`
4. 打通积分和成就闭环
5. 实现 `get_morning_brief`
6. 实现 `get_daily_settlement`
7. 实现 `list_rewards` 与 `redeem_reward`
