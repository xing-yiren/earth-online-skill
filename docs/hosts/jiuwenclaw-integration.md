# Jiuwenclaw Integration Guide

> 说明如何将地球Online Skill 作为原型接入 jiuwenclaw，并验证最小链路是否可用。

---

## 1. 当前接入目标

当前仓库中的 jiuwenclaw 接入仍然是原型态，目标是先打通：

- 读取宿主 memory
- 组装 `host_context`
- 跑通 init / onboarding
- 为后续任务、晨报、结算接入做准备

当前不做：

- 自动安装到 jiuwenclaw 的技能目录
- 自动注册宿主触发器
- 深度依赖 jiuwenclaw 私有运行时 API

---

## 2. 依赖的本地宿主结构

当前 `JiuwenclawAdapter` 默认读取：

```text
C:\Users\<user>\.jiuwenclaw\agent\
  memory\
    USER.md
    MEMORY.md
    messages.json
```

其中：

- `USER.md`：提供用户基本画像
- `MEMORY.md`：提供长期 memory facts
- `messages.json`：提供最近用户消息

当前适配器以只读方式读取这些文件，不会修改宿主目录内容。

---

## 3. 接入步骤

### Step 1: 准备地球Online 仓库

确保当前仓库可运行，并已安装 Python 环境。

建议先执行：

```bash
python scripts/smoke_test.py
```

确认 Skill 核心原型本身可运行。

### Step 2: 验证 adapter 到 onboarding 的链路

运行：

```bash
python scripts/adapter_smoke_test.py
```

这一步会：

- 从本地 `.jiuwenclaw/agent/memory/` 读取宿主信息
- 构造标准 `host_context`
- 调用 `init_skill_profile`
- 输出结构化结果

### Step 3: 检查输出重点

重点看：

- `host_context.host.platform` 是否为 `jiuwenclaw`
- `host_context.user.id` 是否存在
- `host_context.session.current_date` 是否存在
- `host_context.context.uncertainties` 是否合理
- `init_result.next_action` 是否合理

如果 `next_action = ask_required_fields`，说明 adapter 识别出存在不确定项，宿主应继续向用户确认。

### Step 4: 进入宿主侧联调

在 jiuwenclaw 正式接入时，建议流程是：

1. 宿主触发 Skill
2. `JiuwenclawAdapter` 组装 `host_context`
3. 先调用 `init_skill_profile`
4. 若未初始化或有必问项，Agent 与用户对话确认
5. 调用 `apply_init_config`
6. 初始化完成后，才进入 `create_task` / `complete_task` / `get_morning_brief` 等主链路

---

## 4. 当前已知问题

### 4.1 用户名与 Agent 名可能混淆

在 jiuwenclaw 的 `USER.md` / `messages.json` 中，可能同时出现：

- 用户自己的名字
- 用户给 Agent 起的称呼

当前 `JiuwenclawAdapter` 已开始通过 `uncertainties` 输出不确定信号，但这仍是一个需要宿主侧对话确认的问题。

### 4.2 messages.json 中会有噪音消息

当前 adapter 已做一层简单过滤，但仍可能出现：

- 低价值命令
- 宿主历史任务噪音
- 与地球Online 无关的近期消息

这部分需要在后续版本里继续优化策略。

---

## 5. 当前最推荐的接入姿势

对于 jiuwenclaw，当前最推荐的方式是：

- 先把本仓库作为独立原型仓库维护
- 用 adapter 读取宿主上下文
- 用 `host_context` 驱动 init 与主工具
- 不在现阶段把 Skill 逻辑直接写死到 jiuwenclaw 私有格式中

也就是说：

- `SKILL.md` 继续保持通用
- jiuwenclaw 的差异留在 adapter 层和宿主接入层

---

## 6. 当前接入完成标准

当满足以下条件时，可以认为 jiuwenclaw 第一版接入成立：

1. `adapter_smoke_test.py` 输出结构完整
2. `init_skill_profile` 能根据 `uncertainties` 返回合理 `next_action`
3. 用户完成初始化后，可在宿主中调用基础主链路工具
4. 晨间签到、任务完成、奖励兑换至少能跑通一条真实调用链
