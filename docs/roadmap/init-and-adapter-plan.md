# Init, Onboarding, and Adapter Plan

> 定义地球Online 在接入真实宿主平台前的初始化流程，以及它与 Host Adapter 的配合方式

---

## 1. 目标

地球Online 不应假设运行时状态天然存在。

在真实宿主接入场景下，Skill 需要一套明确的初始化流程，用来：

- 从宿主 `host_context` 读取可用默认信息
- 判断当前 Skill 是否已初始化
- 生成初始配置建议
- 引导用户确认关键设定
- 初始化本地运行时状态

同时，这套流程需要与 Host Adapter 明确协作，而不是让 Skill 直接依赖宿主私有 memory 结构。

---

## 2. 初始化流程原则

### 2.1 宿主负责提供上下文

宿主平台通过 Host Adapter 提供：

- `user.id`
- `user.name`
- `user.timezone`
- `context.preferences`
- `context.memory_facts`

### 2.2 Skill 负责生成建议配置

地球Online 根据宿主上下文生成建议初始配置，而不是自行假设所有字段都已经齐全。

### 2.3 Agent 负责对话确认

如果关键配置缺失，应该由宿主 Agent 与用户对话确认，而不是由底层脚本直接做人机问答。

### 2.4 初始化工具负责落盘

在用户完成确认后，由初始化工具将确认后的配置写入 `runtime/data/`。

---

## 3. 推荐拆分的两个工具

### 3.1 `init_skill_profile`

职责：

- 检查当前 runtime 是否已初始化
- 从 `host_context` 读取可用默认值
- 生成建议配置
- 标记缺失字段和建议提问项

### 3.2 `apply_init_config`

职责：

- 接收用户确认后的配置
- 在 `runtime/data/` 中创建初始状态文件
- 将 `examples/seed-data/` 作为模板拷贝并覆盖必要字段
- 标记 Skill 已初始化

---

## 4. 首次配置建议字段

### 必问

- 你希望我怎么称呼你
- 你的时区是什么
- 默认几点算晨间目标时间
- 早起宽限几分钟

### 建议问

- 你更喜欢哪种表达风格：轻度 / 标准 / 热血

### 可后置

- 初始 habit list
- 初始 reward list

---

## 5. 与 Host Adapter 的关系

### Host Adapter 负责

- 提供统一 `host_context`
- 从宿主读取用户 profile / memory / session
- 提供可用于默认配置的建议值

### Init 工具负责

- 消化 `host_context`
- 生成建议 profile
- 创建运行时状态

### Skill 业务工具负责

- 在初始化完成后，消费 `runtime/data/` 和 `host_context`
- 不负责首次引导本身

---

## 6. 推荐开发顺序

### Phase A

1. 新增 `runtime/data/` 初始化逻辑
2. 设计 `init_skill_profile`
3. 设计 `apply_init_config`

### Phase B

1. 实现 `jiuwenclaw adapter` 示例
2. 实现 `qclaw adapter` 示例
3. 实现 `openclaw` adapter 协议映射示例

### Phase C

1. 用 adapter + init 流程跑通首次接入
2. 再把晨报、任务、结算、奖励接入真实宿主

---

## 7. 时间建议

如果按当前仓库基础推进，我建议的粗略节奏是：

- Init/onboarding 设计与落地：1-2 天
- `jiuwenclaw adapter` 示例：1-2 天
- `qclaw adapter` 示例：1-2 天
- `openclaw` 协议映射示例：0.5-1 天
- 接入联调与修正：1-2 天

整体上，下一阶段可以按 **5-9 天的原型落地窗口** 预估。

---

## 8. 现阶段建议

当前仓库已经完成 Skill 核心原型，下一阶段不建议继续扩张玩法，而应优先：

1. 先补 init/onboarding
2. 再做 adapter 示例
3. 最后进入真实宿主接入
