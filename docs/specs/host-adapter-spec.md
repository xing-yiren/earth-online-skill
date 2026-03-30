# 地球Online Host Adapter Spec

> 定义不同宿主平台如何将自身上下文转换为统一 `host_context`，并安全接入地球Online Skill

---

## 1. 文档目的

`docs/specs/host-context-spec.md` 定义了宿主传给 Skill 的统一上下文结构。

本规范继续向前一步，定义：

- 宿主平台如何组织适配层
- 适配层应该负责什么
- 适配层不应该负责什么
- qclaw / jiuwenclaw 应如何映射到统一 `host_context`

本规范的目标是把“平台差异”限制在 adapter 层，避免污染地球Online Skill 的业务逻辑层。

---

## 2. Host Adapter 定义

Host Adapter 是连接“宿主平台内部结构”和“地球Online Skill 标准接口”之间的一层转换器。

它的任务是：

1. 从宿主平台读取用户、session、memory、recent messages 等信息
2. 将这些信息转换成统一 `host_context`
3. 把 `host_context` 与 Skill 的工具调用参数一起传给地球Online

Host Adapter 不属于地球Online 的游戏规则层，也不属于宿主平台的底层存储层。它是一个明确的中间层。

---

## 3. 设计原则

### 3.1 平台私有，协议统一

各宿主平台可以有完全不同的内部结构，例如：

- qclaw 可能基于 sqlite、workspace、平台目录
- jiuwenclaw 可能基于 `USER.md`、`MEMORY.md`、`messages.json`
- openclaw 也可能有自己的 profile 和 memory 系统

这些内部结构都不应该暴露给地球Online Skill。

Skill 只接收统一 `host_context`。

### 3.2 读取优先，写入克制

V1 阶段的 Host Adapter 以只读提取为主：

- 读取用户信息
- 读取 session 信息
- 读取 memory 摘要
- 读取 recent messages

Adapter 不应直接修改宿主 memory，不应成为宿主数据写入入口。

### 3.3 宿主负责理解，Skill 负责规则

Adapter 所在的宿主侧应负责：

- 用户意图识别
- recent context 组织
- memory 摘要提炼

地球Online Skill 负责：

- 任务状态
- 积分计算
- 成就检查
- 奖励兑换
- 结算输出

### 3.4 Skill 私有状态独立维护

Adapter 不直接读写 Skill 私有状态规则本身，只负责把宿主信息整理给 Skill。

Skill 私有状态包括：

- `tasks.json`
- `points.json`
- `achievements.json`
- `rewards.json`

---

## 4. Adapter 职责边界

### 4.1 Adapter 必须负责的事情

- 识别当前宿主平台
- 提取当前用户标识
- 提取当前日期和时区
- 提取 recent messages
- 提取 memory facts
- 提取偏好信息
- 组装标准 `host_context`
- 在必要时为缺失字段提供安全兜底

### 4.2 Adapter 不负责的事情

- 不负责积分加减逻辑
- 不负责任务状态变更
- 不负责成就判定
- 不负责奖励兑换
- 不负责生成地球Online的最终游戏化文案

这些都应由地球Online Skill 自己完成。

---

## 5. 标准接口建议

Host Adapter 可以先按文档协议设计，也可以后续实现为代码接口。

推荐抽象接口如下：

```python
class HostAdapter:
    def get_platform_info(self) -> dict:
        ...

    def get_user_info(self) -> dict:
        ...

    def get_session_info(self) -> dict:
        ...

    def get_intent_info(self, raw_input: str | None = None) -> dict:
        ...

    def get_context_info(self) -> dict:
        ...

    def build_host_context(self, raw_input: str | None = None) -> dict:
        ...
```

如果暂时不实现为 class，也可以按函数式组织：

```python
def load_platform_info() -> dict: ...
def load_user_info() -> dict: ...
def load_session_info() -> dict: ...
def load_intent_info(raw_input: str | None = None) -> dict: ...
def load_context_info() -> dict: ...
def build_host_context(raw_input: str | None = None) -> dict: ...
```

---

## 6. 标准输出要求

Adapter 的最终输出必须符合 `docs/specs/host-context-spec.md`。

最小输出：

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

推荐输出：

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
    "name": "complete_task",
    "confidence": 0.92,
    "source_text": "项目报告我已经做完了"
  },
  "context": {
    "recent_messages": [
      "我今天要完成项目报告",
      "项目报告我已经做完了"
    ],
    "memory_facts": [
      "本周需要交项目报告",
      "最近在准备面试"
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

## 7. 字段提取建议

### 7.1 `host`

至少提取：

- `platform`

推荐补充：

- `platform_version`
- `skill_runtime_version`

### 7.2 `user`

至少提取：

- `id`

推荐补充：

- `name`
- `timezone`

### 7.3 `session`

至少提取：

- `current_date`

推荐补充：

- `session_id`
- `current_time`

### 7.4 `intent`

推荐由宿主 Agent 输出：

- `name`
- `confidence`
- `source_text`

如果宿主暂时不提供 `intent`，Skill 仍可在受限模式下运行，但不建议长期依赖这种模式。

### 7.5 `context`

推荐提取：

- `recent_messages`
- `memory_facts`
- `preferences`

这些字段的作用是：

- `recent_messages`: 帮助 Skill 理解当前任务语境
- `memory_facts`: 帮助 Skill 了解长期背景
- `preferences`: 帮助 Skill 决定文案风格与呈现方式

---

## 8. 校验与兜底规则

### 8.1 校验规则

Adapter 输出前，建议至少做以下校验：

- `host.platform` 非空
- `user.id` 非空
- `session.current_date` 为合法 `YYYY-MM-DD`

### 8.2 缺失字段兜底

如果字段缺失，可按以下规则降级：

- 缺 `user.name` -> 由 Skill 用默认昵称 `玩家`
- 缺 `user.timezone` -> 默认 `Asia/Shanghai`
- 缺 `context.preferences` -> 使用标准游戏化风格
- 缺 `context.recent_messages` -> 使用空数组
- 缺 `context.memory_facts` -> 使用空数组

### 8.3 非法数据处理

如果最小字段缺失，Adapter 应返回结构化错误，而不是让 Skill 自己猜测：

```json
{
  "success": false,
  "error": "invalid_host_context",
  "message": "missing required field: user.id"
}
```

---

## 9. 适配流程建议

标准流程如下：

1. 宿主接收到用户输入或定时触发
2. 宿主 Agent 做语义理解与意图识别
3. Host Adapter 从宿主读取用户、session、memory、recent messages
4. Host Adapter 生成标准 `host_context`
5. 宿主调用地球Online Skill 工具，并传入 `host_context`
6. 地球Online Skill 读取自身状态并执行业务逻辑
7. Skill 返回结构化结果，宿主负责最终对话呈现

---

## 10. qclaw 适配建议

基于当前观察到的目录结构，qclaw 具备：

- `memory/`
- `workspace/`
- `cron/`
- `agents/`
- `plugins/`

并已观察到：

- `memory/main.sqlite`
- `workspace/earth-online-data`

### qclaw adapter 建议职责

- 从 qclaw 的 memory / profile 中提取用户信息
- 从 qclaw 当前会话或相关上下文中提取 recent messages
- 从宿主 memory 中整理出 `memory_facts`
- 构建统一 `host_context`

### qclaw adapter 应避免

- 直接把 sqlite 结构暴露给 Skill
- 在 Skill 内写死 `.qclaw` 目录路径
- 让 Skill 自己去猜 qclaw 的内部数据布局

### qclaw V1 适配优先级

建议先做到：

1. 能提取 `user.id`
2. 能提取 `current_date`
3. 能传入 `recent_messages`
4. 再逐步补 `memory_facts` 和 `preferences`

---

## 11. jiuwenclaw 适配建议

基于当前观察到的目录结构，jiuwenclaw 具备：

- `agent/memory/USER.md`
- `agent/memory/MEMORY.md`
- `agent/memory/messages.json`
- `agent/skills/`
- `agent/sessions/`

### jiuwenclaw adapter 建议职责

- 从 `USER.md` 提取用户基础信息
- 从 `MEMORY.md` 提取长期 memory facts
- 从 `messages.json` 提取 recent messages
- 从 session 或运行时提取当前日期、时间和触发方式
- 组装统一 `host_context`

### jiuwenclaw adapter 优势

由于 `USER.md`、`MEMORY.md` 和 `messages.json` 结构更直观，jiuwenclaw 很适合作为第一个落地 adapter 示例。

### jiuwenclaw adapter 应避免

- 让 Skill 直接读取这些宿主文件
- 在 Skill 业务逻辑中出现 `agent/memory/` 这种宿主路径依赖

---

## 12. openclaw 适配建议

虽然当前尚未直接查看其本地结构，但接入原则应与前两者一致：

- 宿主内部结构保持私有
- Host Adapter 负责转换
- 输出统一 `host_context`
- Skill 业务层保持完全无平台感知

建议在文档层先定义 adapter 接口，再在实现阶段补各平台示例。

---

## 13. 文件组织建议

后续如果进入实现阶段，建议在项目内加入类似结构：

```text
adapters/
  base_adapter.py
  qclaw_adapter.py
  jiuwenclaw_adapter.py
  openclaw_adapter.py
  kimiclaw_adapter.py
```

其中：

- `base_adapter.py` 定义抽象接口或通用 helper
- 各平台 adapter 只负责宿主上下文提取与转换

---

## 14. 验收标准

一个 Host Adapter 至少要满足以下要求：

1. 能生成合法的最小 `host_context`
2. 平台私有实现不会泄漏到 Skill 业务层
3. 缺失字段时能提供清晰兜底或报错
4. 不直接修改宿主 memory
5. 可以稳定服务于 `create_task`、`complete_task`、`get_morning_brief`、`get_daily_settlement`

---

## 15. 推荐后续顺序

基于本规范，建议后续开发顺序为：

1. 先补充 `docs/specs/data-and-tools-spec.md` 中工具对 `host_context` 的强约束说明
2. 设计 `base_adapter` 抽象接口
3. 先实现 `jiuwenclaw adapter` 示例
4. 再实现 `qclaw adapter` 示例
5. 然后进入最小 Skill 工具闭环实现：
   - `create_task`
   - `complete_task`
   - `get_morning_brief`
   - `get_daily_settlement`
