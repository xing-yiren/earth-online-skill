# 地球Online Host Context Spec

> 定义宿主平台如何向地球Online Skill 提供统一上下文

---

## 1. 文档目的

本规范用于解决一个核心问题：

不同宿主平台（如 qclaw、openclaw、jiuwenclaw）拥有不同的 memory、session 和 profile 结构时，地球Online Skill 应如何以统一方式接收上下文。

本规范的目标是：

- 让地球Online 不直接依赖宿主私有目录结构或文件格式
- 让不同宿主平台通过适配层输出统一 `host_context`
- 让 Skill 业务层只关心任务、积分、成就和奖励规则

---

## 2. 设计原则

### 2.1 宿主优先

宿主平台负责：

- 用户身份与 profile
- memory
- recent messages
- session
- intent 识别
- tool 调度

地球Online 不重复实现这些宿主能力。

### 2.2 Skill 私有状态独立

地球Online Skill 只维护自身业务状态：

- tasks
- points
- achievements
- rewards

### 2.3 协议优先于文件格式

Skill 不应直接依赖以下宿主私有实现：

- `MEMORY.md`
- `USER.md`
- `messages.json`
- sqlite 数据库
- 宿主特定目录路径

Skill 只依赖宿主传入的 `host_context`。

### 2.4 降级可用

如果宿主暂时无法提供完整上下文，Skill 可以用本地默认配置降级运行，但这不应成为正式跨平台接入的主模式。

---

## 3. Host Context 总体结构

标准结构如下：

```json
{
  "host": {},
  "user": {},
  "session": {},
  "intent": {},
  "context": {},
  "runtime": {}
}
```

说明：

- `host`: 宿主平台信息
- `user`: 当前用户信息
- `session`: 当前会话与时间信息
- `intent`: 宿主识别出的用户意图
- `context`: 近期上下文与 memory 摘要
- `runtime`: 宿主运行时补充信息

---

## 4. 最小可用结构

这是宿主接入地球Online 时必须至少提供的字段：

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

### 最小字段说明

- `host.platform`: 当前宿主平台标识
- `user.id`: 当前用户唯一标识
- `session.current_date`: 当前业务日期，用于结算、daily 任务和 streak 判断

没有这 3 个字段，Skill 无法稳定运行。

---

## 5. 推荐结构

建议宿主尽量提供以下完整上下文：

```json
{
  "host": {
    "platform": "jiuwenclaw",
    "platform_version": "0.1.0",
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
    "current_time": "2026-03-25T07:10:00+08:00"
  },
  "intent": {
    "name": "create_task",
    "confidence": 0.93,
    "source_text": "我今天要完成项目报告"
  },
  "context": {
    "recent_messages": [
      "我今天要完成项目报告",
      "还有面试要准备"
    ],
    "memory_facts": [
      "最近在准备面试",
      "本周需要交项目报告"
    ],
    "preferences": [
      "喜欢游戏化表达",
      "不喜欢太正式的语气"
    ]
  },
  "runtime": {
    "trigger": "user_message",
    "locale": "zh-CN"
  }
}
```

---

## 6. 字段定义

### 6.1 `host`

```json
{
  "platform": "qclaw",
  "platform_version": "0.1.0",
  "skill_runtime_version": "1.0"
}
```

字段说明：

- `platform`: 必填。宿主平台标识，例如 `qclaw`、`jiuwenclaw`
- `platform_version`: 可选。宿主版本
- `skill_runtime_version`: 可选。宿主为 Skill 提供的运行时版本

### 6.2 `user`

```json
{
  "id": "demo-user",
  "name": "DemoUser",
  "timezone": "Asia/Shanghai"
}
```

字段说明：

- `id`: 必填。用户唯一标识
- `name`: 推荐。用于播报和文案展示
- `timezone`: 推荐。用于 date、daily 任务和 streak 判断

### 6.3 `session`

```json
{
  "session_id": "sess_001",
  "current_date": "2026-03-25",
  "current_time": "2026-03-25T07:10:00+08:00"
}
```

字段说明：

- `session_id`: 可选。当前会话标识
- `current_date`: 必填。当前业务日期，格式 `YYYY-MM-DD`
- `current_time`: 推荐。完整时间戳

### 6.4 `intent`

```json
{
  "name": "complete_task",
  "confidence": 0.92,
  "source_text": "项目报告我已经做完了"
}
```

字段说明：

- `name`: 推荐。宿主识别出的意图
- `confidence`: 可选。识别置信度
- `source_text`: 可选。触发本次调用的原始文本

推荐意图值：

- `morning_brief`
- `create_task`
- `complete_task`
- `daily_settlement`
- `list_rewards`
- `redeem_reward`
- `unknown`

### 6.5 `context`

```json
{
  "recent_messages": [],
  "memory_facts": [],
  "preferences": []
}
```

字段说明：

- `recent_messages`: 推荐。最近相关对话，按时间顺序排列
- `memory_facts`: 推荐。从宿主 memory 中提炼出的事实
- `preferences`: 推荐。用户表达风格偏好、行为偏好等

可选扩展字段：

- `calendar_summary`
- `today_focus`
- `energy_state`
- `last_settlement_summary`

### 6.6 `runtime`

```json
{
  "trigger": "user_message",
  "locale": "zh-CN"
}
```

字段说明：

- `trigger`: 可选。触发方式，如 `user_message`、`cron`、`manual`
- `locale`: 可选。语言环境

---

## 7. 字段优先级与使用规则

### 7.1 用户展示名

优先级：

1. `host_context.user.name`
2. 本地 `examples/seed-examples/seed-examples/seed-data/USER.md` 默认值
3. 兜底为 `玩家`

### 7.2 时区

优先级：

1. `host_context.user.timezone`
2. 本地 `examples/seed-examples/seed-examples/seed-data/USER.md`
3. 默认 `Asia/Shanghai`

### 7.3 用户偏好

优先级：

1. `host_context.context.preferences`
2. 宿主默认 profile 配置
3. Skill 默认风格

### 7.4 任务意图

优先级：

1. `host_context.intent.name`
2. 宿主传入的结构化动作
3. 不建议由 Skill 再回退做强正则识别

原则：任务主识别由宿主 Agent 负责，地球Online 只负责业务规则映射与状态更新。

---

## 8. Host Adapter 责任

每个宿主平台应实现自己的 `Host Adapter`，负责将平台私有结构映射为统一 `host_context`。

### Adapter 应负责

- 读取宿主用户 profile
- 读取最近对话上下文
- 读取宿主 memory 摘要
- 提取用户偏好
- 生成标准 `host_context`

### Adapter 不应负责

- 执行地球Online 的积分逻辑
- 执行成就判定
- 修改 Skill 私有状态

这些逻辑都应属于地球Online Skill 自身。

---

## 9. 平台映射建议

### 9.1 qclaw

已观察到 qclaw 具有如下特征：

- 平台级目录较完整
- 存在 `memory/main.sqlite`
- 存在 `workspace/`

建议：

- 从 qclaw 的 memory/profile/session 中提取用户信息
- 从 qclaw 的 workspace 中挂载 Skill 私有状态目录
- 通过 qclaw adapter 统一输出 `host_context`

### 9.2 jiuwenclaw

已观察到 jiuwenclaw 具有如下特征：

- 存在 `agent/memory/USER.md`
- 存在 `agent/memory/MEMORY.md`
- 存在 `agent/memory/messages.json`
- 存在 `agent/skills/`

建议：

- 优先从 `USER.md` 提取用户基础信息
- 从 `MEMORY.md` 和 `messages.json` 整理 memory facts 与 recent messages
- 由 jiuwenclaw adapter 输出统一 `host_context`

### 9.3 openclaw

虽然当前未直接检视其本地目录，但建议采用相同适配策略：

- 宿主平台内部结构保持私有
- 统一通过 adapter 输出标准 `host_context`
- 地球Online Skill 不感知平台内部差异

---

## 10. 降级与兜底策略

如果宿主暂时只能提供最小上下文，Skill 应允许降级运行。

### 降级策略

- 缺少 `user.name` 时，用本地默认昵称
- 缺少 `timezone` 时，用默认时区
- 缺少 `preferences` 时，用标准游戏化风格
- 缺少 `recent_messages` / `memory_facts` 时，Skill 仍可执行基础任务管理和结算

### 非推荐策略

以下方式只作为开发调试兜底，不作为正式跨平台接入标准：

- 直接读取 `examples/seed-examples/seed-examples/seed-data/MEMORY.md`
- 直接读取宿主私有 sqlite
- 在 Skill 内硬编码 `.qclaw` 或 `.jiuwenclaw` 路径

---

## 11. 与工具接口的关系

推荐所有核心工具都支持可选 `host_context` 输入。

适用工具包括：

- `get_morning_brief`
- `create_task`
- `complete_task`
- `get_daily_settlement`
- `list_rewards`
- `redeem_reward`

说明：

- `host_context` 是宿主到 Skill 的标准输入协议
- Skill 私有状态文件是 Skill 内部状态来源
- 两者共同决定最终输出

---

## 12. 验收标准

本规范成立后，应满足以下条件：

1. 地球Online 不直接依赖任一宿主私有 memory 文件格式
2. 宿主可通过最小 `host_context` 接入 Skill
3. qclaw 与 jiuwenclaw 可以分别通过 adapter 输出同构上下文
4. Skill 工具层可以稳定接收 `host_context`
5. 业务层无需感知宿主平台差异

---

## 13. 后续工作建议

基于本规范，后续开发顺序建议为：

1. 为 `docs/specs/data-and-tools-spec.md` 中所有核心工具固定 `host_context` 输入约定
2. 设计 `Host Adapter` 抽象接口
3. 先实现 `jiuwenclaw adapter` 示例
4. 再实现 `qclaw adapter` 示例
5. 最后进入 Skill 工具闭环实现
