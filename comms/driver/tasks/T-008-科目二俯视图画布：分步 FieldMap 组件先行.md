---
id: T-008
title: 科目二俯视图画布：分步 FieldMap 组件先行（T-007 的画笔）
owner: cursor
status: review
priority: P0
depends: 
created: 2026-10-16 22:00
updated: 2026-10-16 22:18
---
## 目标

T-007（科目二骨架重设计）要给每个项目页配静态分步俯视图。把「画笔」拆出来先行：
一个纯呈现的分步俯视图组件 + 倒车入库的几何草表，全部落在新文件里，与 T-004
（subject2.dart）、T-006（content/subject2.json）零冲突，**立刻可开工、可并行**。

## 交付

1. `lib/subject2/field_map.dart`：`FieldMapStep` 数据类（车身位姿 x/y/heading、
   方向盘角度、参照物高亮标记、库位与控制线几何）+ `FieldMapPainter`
   （CustomPainter：库位线框、控制线、带朝向的车身矩形、方向盘圆盘）+
   `FieldMap` widget（吃 `List<FieldMapStep>` 与当前步序号）。
2. 倒车入库右倒库 7 步的几何草表（Dart 常量）。位姿按示意图合理赋值即可——
   是「示意」不是测绘，教学重点是相对关系（车身与库角、控制线的位置关系）。
3. widget test：给定几何能渲染、切换步骤会重绘；golden 测试可选，不做硬性。
4. 现有 334+ 测试不破坏，`python scripts/check.py driver` 退出码 0。

## 约束

- 只建新文件，不动 `subject2.dart` / `guide.dart` / `home.dart` / `content/subject2.json`。
- Painter 只吃数据不写死步骤；步骤文字标注不做——四行决策点由 T-007 的项目页负责，
  本组件只画图。
- 简笔风格先落地（车=带朝向的矩形+方向盘圆盘、库位=线框、参照物=高亮标记），
  精致化等骨架验收后再说（ADR 0040：篇幅与掌握目标匹配，图同理）。

## 验收

1. 组件按草表可渲染 7 步且步骤切换重绘（测试断言即可，不要求临时 demo 入口）。
2. 截图放 `comms/driver/artifacts/T-008/`。
3. 测试全绿 + check 通过，证据（diff + 截图）同目录。

## 进展记录
- [2026-10-16 22:12] cursor：todo → doing · T-006 前半已交 review。开始 field_map.dart，只做倒库 7 步草表。
- [2026-10-16 22:18] cursor：doing → review · field_map.dart + reverseParkSketch 7 步。换步重绘有测试。截图 comms/driver/artifacts/T-008/reverse-step-0/2/4/6.png。check.py driver 退出码 0，343 测试通过，Built athena-driver.exe。未动 subject2.dart、guide.dart、home.dart、subject2.json，也没做 step_flow 和另外三项草表。
