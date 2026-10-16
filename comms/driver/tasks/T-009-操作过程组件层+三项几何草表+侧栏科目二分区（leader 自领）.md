---
id: T-009
title: 操作过程组件层 + 其余三项几何草表 + 侧栏科目二分区（leader 自领）
owner: zcode
status: doing
priority: P0
depends: T-004（仅第 3 块；组件与草表无依赖）
created: 2026-10-16 22:10
updated: 2026-10-16 22:10
---
## 背景

使用者定调科目二骨架重设计（T-007）后要求多智能体分摊并行。leader 自领与 cursor
线文件零冲突的三块，双线满负荷；cursor 线不变（T-008 → T-006 → T-007）。

## 交付（zcode 做）

1. **`lib/subject2/step_flow.dart`（立刻）**：操作过程组件层——`StepFlow` widget：
   步骤条（N 步、点选切换）、决策点渲染（reference「盯哪」/ steer「做什么」为主角行，
   focus/action/done 次行，skill 附注）、警示区（fix「偏了怎么修」警示色块、
   wrong「别按这个」红、caution 红条，三者色系区分）、车内/车外双视角分栏容器
   （宽屏左右、窄屏纵向，风格对齐 drill 的 CabinPanel）。输入模型全可选、字段名与
   T-006 定稿对齐，测试用造数据，不依赖 T-006 落地。
2. **其余三项几何草表**：侧方停车 / 曲线行驶 / 直角转弯每步一份几何参数，数据形态
   与 T-008 的倒库草表一致（以先落地者为准，后做的一方对齐）；文件随 T-008 的结构
   约定（若 T-008 单文件则按项目分段文件，避免两人写同一文件）。
3. **侧栏科目二分区改版（T-004 提交后动 home.dart）**：四项目 + 注意事项 + 考试流程
   （考试日怎么走），项目条目不显示题数；「待练 N 题」「合格标准与通用评判」撤出
   侧栏一级（归口方式见 T-007）。

## 约束

- 只动 `step_flow.dart`、三个草表文件、`home.dart`（T-004 提交后）；不碰
  `subject2.dart` / `guide.dart` / `content/subject2.json` / `field_map.dart`。
- 组件在被项目页引用前保持可独立测试。
- `python scripts/check.py driver` 退出码 0，现有 334+ 测试不破坏。

## 验收

1. StepFlow 渲染断言（步骤条、决策点行、警示区、双视角标签）+ 宽窄截图放
   `comms/driver/artifacts/T-009/`。
2. 侧栏断言（四项目+注意事项+考试流程、无题数）。
3. 测试全绿 + check 通过。

## 进展记录
