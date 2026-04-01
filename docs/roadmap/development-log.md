# Development Log

> 记录地球Online Skill 原型在当前仓库中的阶段性开发进展与下一步计划。

---

## 2026-03-30

### 本次完成

- 完成仓库公开结构重构，整理为 `docs/`、`examples/seed-data/`、`runtime/`、`scripts/`
- 将文档迁移到 `docs/`，并补充了 `init-and-adapter-plan.md`
- 完成核心服务层：
  - `TaskService`
  - `PointsService`
  - `AchievementService`
  - `SettlementService`
  - `RewardService`
- 完成工具层：
  - `create_task`
  - `complete_task`
  - `get_morning_brief`
  - `get_daily_settlement`
  - `list_rewards`
  - `redeem_reward`
  - `record_morning_checkin`
- 完成 runtime 初始化第一版：
  - `init_skill_profile`
  - `apply_init_config`
- 升级 `init_skill_profile` 输出结构，补充：
  - `required_fields`
  - `optional_fields`
  - `defaulted_fields`
  - `next_action`
- 完成 `scripts/smoke_test.py`，并多次验证最小闭环可运行
- 建立 adapter 骨架：
  - `BaseHostAdapter`
  - `JiuwenclawAdapter`
- 将 `JiuwenclawAdapter` 升级为第一版真实读取实现：
  - 读取 `USER.md`
  - 读取 `MEMORY.md`
  - 读取 `messages.json`
  - 组装标准 `host_context`
- 优化 `JiuwenclawAdapter` 的解析策略：
  - 更谨慎地区分用户名称与 Agent 称呼
  - 清洗 `messages.json` 中的低价值消息
  - 对备注中的 Agent 别名和偏好信息做拆分
- 引入 adapter -> onboarding 的不确定信号机制：
  - adapter 输出 `context.uncertainties`
  - init 工具据此决定是否继续确认用户称呼
- 修正 onboarding 对 uncertainty 的消费逻辑：
  - `user_name_missing` 会触发 `name` 必问
  - `timezone_missing` 会触发 `timezone` 必问
  - `next_action` 能正确切换到 `ask_required_fields`
- 新增 adapter 测试脚本：
  - `scripts/adapter_smoke_test.py`
- 补充 jiuwenclaw 文档：
  - 接入说明
  - 覆盖场景测试清单
  - 对话式测试 prompts
- 升级 `adapter_smoke_test.py` 输出：
  - 增加 `checks` 摘要
  - 更适合作为接入检查脚本
- 清理 `examples/seed-data/` 为真正的新玩家模板：
  - 初始积分归零
  - 初始任务清空
  - 初始成就清空
  - memory 调整为中性模板
- 为 onboarding 增加防呆约束：
  - `apply_init_config` 需要 `confirmed_by_user = true`
  - `required_fields` 未确认时拒绝执行
- 调整 `init_skill_profile` 输出语义：
  - 将不可信字段与 fallback 默认值拆开
  - 不再把 `DemoUser` / `Asia/Shanghai` 误当成已确认用户信息
- 更新 `smoke_test.py`：
  - 改为先创建任务再完成任务
  - 适配新的 clean seed data
- 修复工具入口的可执行性：
  - 为核心 tool 增加统一 bootstrap
  - 支持从不同工作目录直接执行
  - 降低 `ModuleNotFoundError: No module named 'scripts.core'` 风险
- 修复 bootstrap 的自举顺序问题：
  - 先注入项目根到 `sys.path`
  - 再导入 `scripts.tools._bootstrap`
  - 验证从仓库根与 `scripts/tools/` 目录直接执行均可工作

### 当前状态

- Skill 核心原型已可运行
- 运行态与示例种子数据已分离
- 当前重点已从“纯原型实现”切换到“宿主接入准备”
- init/onboarding 已进入可供 Agent 编排的第一版结构化阶段
- `JiuwenclawAdapter` 已进入可读取本地宿主信息的第一版实现阶段
- `JiuwenclawAdapter` 已开始从“能跑”向“更可靠可用”收口
- onboarding 已能消费 adapter 输出的不确定性信号
- jiuwenclaw 已具备“对接说明 + 测试清单 + adapter 冒烟验证脚本”的第一版落地材料
- `JiuwenclawAdapter -> init_skill_profile` 链路已经验证可用
- 初始化链已开始具备“不能跳过必问项”的约束能力

### 下一步

- 让 adapter 输出的 `host_context` 与 init 工具联动
- 验证 `JiuwenclawAdapter -> init_skill_profile` 的初始化链
- 再开始规划 `qclaw adapter`
- 继续评估真实宿主 memory 数据中的噪音清洗策略
- 细化 onboarding 里的必问项、建议项与后置项
- 开始抽象 `qclaw adapter` 的最小读取接口
- 准备在 jiuwenclaw 宿主中做真实接入试验，并根据结果回收问题
- 继续验证宿主在真实对话中是否遵守 onboarding 约束
- 后续再推进：
  - `qclaw adapter`
  - `openclaw` 协议映射示例

---

## 日志维护约定

- 每个阶段完成后补一条简要记录
- 每条记录至少包含：
  - 本次完成
  - 当前状态
  - 下一步
- 该日志用于追踪开发节奏，不替代 PRD 或协议文档
