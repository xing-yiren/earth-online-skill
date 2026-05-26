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

---

## 2026-04 ~ 2026-05

### 本次完成

**Claude Code 原生 Skill 安装与触发**
- 在 `.claude/skills/earth-online-skill/SKILL.md` 安装项目级 skill 入口
- Skill 能正确命中并调用 `scripts/tools/*`，优先使用工具返回的 `message`
- 修复 CLI 参数兼容（同时支持 JSON 与 `key=value` 格式）

**真实对话渲染层 (Renderer Layer)**
- 新增 `scripts/renderers/` 目录，将结构化结果转为自然语言中文回复
- 覆盖全部工具：晨间签到、早安播报、任务 CRUD、每日结算、奖励列表/兑换、初始化、候选导入
- 工具统一在 `render=true` 时返回 `message` 字段

**游戏化建档体验 (Game-Style Init)**
- 重写 `init_renderer.py`：角色创建表单式界面（`╔══╗` 边框、"系统自检中..." 过渡语言）
- 支持自动检测玩家信息（从系统/Git/会话上下文推断默认值）
- "玩家称号"替代"称呼"，"系统检测默认值"替代"默认可用"
- 默认名称警告：当称号仍为"玩家"时主动提示修改
- 兼容 `confirmed_fields` 的 dict 格式传入

**任务管理增强**
- 新增 `list_active_tasks` / `update_task` / `cancel_task` 工具
- `update_task` 支持改名、改截止时间、改积分、改类型
- `cancel_task` 替代删除，状态标记为 cancelled
- TaskService 的 `_match_tasks` 忽略 cancelled 任务

**生存天数与成就系统**
- `AchievementService` 新增 `active_dates` 追踪
- `survival_days` 基于真实活跃天数计算
- Seed data 包含 `active_dates` 字段

**CLI 命令行模式**
- 支持 `/earth-online-skill init|checkin|tasks|create|settle|rewards|scan`
- 支持 `地球online 任务|结算|扫描` 等中文别名
- 在 SKILL.md 中定义命令→工具映射表

**跨会话任务扫描 (Cross-Session Scanner)**
- 新增 `scripts/core/session_scanner.py`
- 扫描 `~/.claude/projects/*/` 下所有会话的 `.jsonl` 文件
- 三级数据源：项目文件（CLAUDE.md/TODO.md）> 会话对话 > 项目方向摘要
- 质量评分系统 (0-10)：任务指示词匹配 + 长度奖励 + 实质产出物 + 时间承诺
- 琐碎模式黑名单：过滤"好的""提交commit""继续"等非任务消息
- 项目方向级摘要：自动合成"继续推进 XX 项目"类候选
- 安全约束：必须用户明确授权才扫描

**工具基础设施**
- `_bootstrap.py` 支持 JSON 和 `key=value` 两种参数格式
- `print_result()` 强制 `sys.stdout.reconfigure(encoding="utf-8")` 解决 Windows 中文乱码
- `session_scanner` 支持 `_EO_SESSION_SCAN_ROOT_OVERRIDE` 环境变量便于测试

**测试体系**
- `smoke_test.py` — 核心闭环（8 个场景，含 render 验证）
- `dialogue_edge_smoke_test.py` — 对话边界（重复、歧义、幂等、取消）
- `onboarding_smoke_test.py` — 初始化 + 候选导入
- `cli_smoke_test.py` — CLI 子进程 JSON 入参验证
- `adapter_smoke_test.py` — adapter 原型验证
- `session_scan_smoke_test.py` — 跨会话扫描验证

**候选任务导入 (Onboarding Import)**
- `OnboardingImportService.suggest_candidates()` — 生成候选，不写任务
- `OnboardingImportService.apply_candidates()` — 用户确认后批量写入
- 支持 `raw_candidates` 为字符串或带字段 dict
- 建档后**必须**推进候选导入，不停在建档消息上
- 主动询问跨会话扫描选项

**目录管理**
- `.gitignore` 忽略 `tmp/`、`.agents/`
- 临时文件移入 `tmp/` 目录

---

## 2026-05-25 ~ 2026-05-26

### 本次完成

**无限流系统风格统一**
- 晨间播报、晚间结算、任务 CRUD、奖励兑换全部采用无限流小说系统风格
- 世界观映射：用户=玩家、每天=副本、任务=主线/支线、完成=通关

**数据卡片架构重构**
- 6 个渲染器从"写死完整文案"转为"输出 `[标签] key:value` 数据骨架"
- SKILL.md 新增"表达风格"规范，Claude 按规范 + 数据卡片自主组织语言
- 解决了之前每条回复都机械"叮！"的问题

**全局 Skill 安装**
- 创建 `~/.claude/skills/earth-online-skill/SKILL.md` 全局入口
- 数据目录 `~/.earth-online/data/` 跨项目共享
- 修复 env var 语法（`set` → inline bash）
- 支持在任意 Claude Code 项目中调用 Earth Online 功能

**定时提醒**
- 早间提醒：每天 08:57
- 晚间提醒：每天 22:07
- 限制：仅在 Claude Code 空闲时触发

**初始化体验增强**
- `init_skill_profile` 新增晨间目标时间、早起宽限、晚间结算时间为可选配置项
- 档案完成后自动推进候选任务导入
- 支持 `confirmed_fields` 的 dict 格式

**跨会话扫描优化**
- 新增项目文件扫描：`CLAUDE.md`、`TODO.md`、`ROADMAP.md` 等
- 新增项目方向摘要：自动合成"继续推进 XX 项目"类候选
- 琐碎模式黑名单过滤
- `create_task` 参数名 `name` 明确文档

**目录与配置**
- `.gitignore` 忽略 `.agents/`、`tmp/`、cron state files
- `_bootstrap.py` 强制 stdout UTF-8 编码

### 当前状态

- v0.4 基本收尾：无限流风格 + 数据卡片架构 + 全局安装 + 定时提醒
- 全量 smoke test 套件持续通过
- 下一阶段：v0.5 测试补齐 + 任务完成追踪 + 任务历史

### 下一步

见 `DEVELOPMENT_PLAN.md`。

---

### 当前状态 (旧)

### 下一步

见 `DEVELOPMENT_PLAN.md`。

---

## 日志维护约定

- 每个阶段完成后补一条简要记录
- 每条记录至少包含：
  - 本次完成
  - 当前状态
  - 下一步
- 该日志用于追踪开发节奏，不替代 PRD 或协议文档
