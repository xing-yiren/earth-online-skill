# 地球Online Skill

> 将日常任务、晨间签到、积分、成就和奖励包装成“地球Online闯关”式的 Skill 原型。

## 简介

地球Online 是一个面向 claw 类宿主平台的 Skill 核心原型。

它的目标不是替代宿主平台的 Agent、Memory 或 Session 系统，而是在宿主之上提供一层游戏化生活体验，把用户的日常推进组织成一套可持续运转的任务与反馈循环。

当前仓库定位为 **prototype**：

- 已完成最小核心闭环
- 已定义宿主接入协议与 adapter 方向
- 尚未包含正式宿主 adapter 实现

## 当前已实现

- 晨间签到与早起 streak
- 创建任务与完成任务
- 积分、等级、成就、奖励
- 早安播报数据聚合
- 每日结算数据聚合
- 最小集成 smoke test

## 项目结构

```text
earth-online-skill/
├── README.md                         # 仓库说明与使用入口
├── SKILL.md                          # Skill 主规范
├── docs/
│   ├── product/
│   │   └── v1-prd.md                 # V1 产品定义
│   ├── specs/
│   │   ├── host-context-spec.md      # 宿主上下文协议
│   │   ├── host-adapter-spec.md      # Adapter 设计规范
│   │   └── data-and-tools-spec.md    # 数据结构与工具接口规范
│   ├── roadmap/
│   │   ├── init-and-adapter-plan.md  # init/onboarding 与 adapter 开发计划
│   │   └── development-log.md        # 开发日志与阶段记录
│   └── demo/
│       └── preview.html              # 效果展示页
├── examples/
│   └── seed-data/                    # 示例种子数据，用于初始化与测试
├── runtime/                          # 本地运行态数据根目录（默认不进 Git）
├── adapters/                         # 宿主 adapter 层
├── scripts/
│   ├── core/                         # 核心服务层
│   ├── tools/                        # 工具入口层
│   └── smoke_test.py                 # 最小集成测试
└── .gitignore
```

## 数据目录说明

- `examples/seed-data/`
  - 仓库内示例种子数据
  - 用于 smoke test 和首次初始化模板

- `runtime/data/`
  - 本地真实运行态数据
  - 默认不进入 Git
  - 首次运行时会由 `examples/seed-data/` 自动初始化

## 快速验证

运行最小集成测试：

```bash
python scripts/smoke_test.py
```

该脚本会在临时数据副本上验证：

- 晨间签到
- 创建任务
- 完成任务
- 晨报
- 每日结算
- 奖励列表
- 奖励兑换

## 文档入口

- [Skill 主规范](SKILL.md)
- [V1 PRD](docs/product/v1-prd.md)
- [Host Context 协议](docs/specs/host-context-spec.md)
- [Host Adapter 规范](docs/specs/host-adapter-spec.md)
- [数据与工具接口规范](docs/specs/data-and-tools-spec.md)
- [Init / Onboarding 与 Adapter 计划](docs/roadmap/init-and-adapter-plan.md)
- [开发日志](docs/roadmap/development-log.md)
- [Jiuwenclaw 对接说明](docs/hosts/jiuwenclaw-integration.md)
- [Jiuwenclaw 测试用例](docs/testing/jiuwenclaw-test-cases.md)

## 下一步计划

下一阶段会优先围绕两个方向推进：

- 完善 `runtime/` 相关能力
  - 明确初始化流程
  - 实现 init / onboarding 工具
  - 让示例种子数据与真实运行态彻底分离

- 实现宿主接入层
  - 补各平台 adapter 示例
