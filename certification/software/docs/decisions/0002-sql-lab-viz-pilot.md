# ADR 0002：SQL 实验试点——viz 组件形态的 lab 块

- 日期：2026-10-09
- 状态：已接受（tiger 确认按试点顺序动工）
- 关系：落地仓库级 [ADR 0091](../../../docs/decisions/0091-experiments-inside-subject-apps.md)
  （实验能力长在学科应用内）；扩展应用级 0001 / 主仓库 [ADR 0058](../../../docs/decisions/0058-content-driven-ui.md)
  的交互形态；校验通过写入进度遵循主仓库 [ADR 0052](../../../docs/decisions/0052-motivation-stats-one-loop.md)

## 背景

内容规划的实践路径评级把第 9 章（数据库技术基础）定为实践性课程：SQL 真跑是
成本最低的编码实验——Rust 侧已有 rusqlite（bundled），教材第 5 版第 9 章 OCR
在库，`swd-ch09` 章树已存在（暂无节）。仓库 ADR 0091 决定编码实验长在学科
应用内，本应用承接其中 SQL 这一类。

## 决策

1. **试点形态：`lab` 走 viz 组件注册表**（`component: "sql-lab"`），不改
   ADR 0058 的九种块类型。实验数据装在 `viz` 块的 `params` 里：
   `setup`（建表与数据的 SQL 数组，在内存库执行）、`task`（题目文字）、
   `answer`（参考查询，其结果集是判定标准）、`hint`（可选提示）。
   铺开到 C、正则、进程同步等多个实验族、`params` 塞不下公共交互时，再立
   ADR 升级为独立块类型；试点不预先抽象。
2. **执行与判定在 Rust 侧**：新增 `run_sql_lab` 命令——`Connection::open_in_memory`
   依次执行 `setup`，执行学习者 SQL，执行参考查询，**行集（列名 + 行）相等即
   通过**；把执行错误原样返回给界面。内存库不落盘，学习者写坏什么都没关系。
3. **校验通过即作答**（ADR 0052）：`run_sql_lab` 返回通过时，前端以
   `mode: "chapter"`、`question_id: <lab id>` 写入一次 `correct` attempt；
   实验不通过不写。掌握率由既有 attempts 派生，不新增表。
4. **编辑器试点用多行文本域 + 等宽字体**，不引入 Monaco：先验证「骨架 → 校验 →
   写进度」闭环；编辑体验的升级（Monaco 本地打包）等实验铺开时一并评估。
5. **出处**：实验所在的节内容取材教材第 9 章 OCR，标 `adapted` + 章节页码
   locator；`lab` 块本身不是判分条目（契约 itemMarkers 只认 `options`），但
   参考查询与建表数据来自教材示例时同样登记教材来源。

## 后果

- 第 9 章新增第一个节（SQL 基础查询）与一个 `sql-lab` 实验，作为形态样板；
  后续节与实验按内容规划排期。
- `run_sql_lab` 是本应用第一个「执行学习者输入」的命令；白名单边界 = 仅内存
  库 + 仅 SQL 语句，无文件与进程访问。
- dsa、c-gui-lab 与本应用的分工见仓库 ADR 0092（dsa 承接第 3、8 章编码实验）。
