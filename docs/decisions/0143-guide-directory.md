# ADR 0143：新增顶层目录 guide/（手册类教程），gtkmm 迁入

- 日期：2026-10-12
- 状态：已接受（使用者要求：新建 `guide/` 存放手册类教程，类似 gtkmm；`subjects/`
  改名 `course/` 稍后另行处理）
- 草拟：[STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V3（ADR 0134 流程，
  落 ADR 前已复看草稿）

## 背景

顶层目录现在按意图分两类（ADR 0060）：`subjects/`（课程学科学习）与 `practice/`
（项目应用）。gtkmm 住在 `subjects/`，但它的定位是「官方教程精读」——《Programming
with gtkmm 4》全量翻译为编排基准，章节编号严格跟随官方文档（gtkmm ADR 0003），
不自编课程大纲。这类「以一本外部手册为蓝本」的应用，与自编教学设计的课程
（大纲→过程→实验三层自上而下，ADR 0028）不是同一种内容组织，混在 `subjects/`
里类别边界模糊。

使用者决定把顶层语义三分：课程类（`course`，现 `subjects/`）、手册类（`guide`）、
项目类（`practice`）；`subjects/`→`course/` 的实际改名稍后另行 ADR。

## 决策

1. **新增顶层目录类别 `guide/`：手册类教程。** 与 `subjects/`、`practice/` 平级，
   一本手册一个独立应用。手册类的定义：以一本外部手册 / 官方教程为蓝本精读学习，
   章节结构与编号跟随原书、不自编大纲。手册类应用是**学习应用**：「跨应用教学规范」
   与进度库（ADR 0037/0053）照常适用——不同的只是「大纲」的来源是手册目录而非自编。
2. **顶层语义三分**：`course`（课程类，自编教学设计）/ `guide`（手册类，跟随原书
   精读）/ `practice`（项目类，做出能跑的东西）。`course` 是 `subjects/` 改名后的
   目标名，改名动作另行 ADR，本条只定语义。
3. **gtkmm 迁入 `guide/`，为首批唯一成员。** id `gtkmm`、进程 `athena-gtkmm`、
   知识点前缀 `gtkmm.`、进度库内容、领域圈 group「程序设计」、出处档位 open
   （ADR 0089）全部不变，纯目录搬家（earth 迁移先例，ADR 0128 补记）。首批不立项
   新手册，等真的决定学哪本时按 new-app 流程单独立项（ADR 0129）。
4. **启动器与统一检查把 `guide/` 当第三个应用根。** `launcher/core` 的发现清单加
   一层 `guide`（顺序：`subjects`、`guide`、`practice`，各层按目录名排）；根
   `scripts/check.py` 的 `APP_ROOTS` 与结构对账同步。仓库根识别仍以 `subjects/`
   为锚（`guide/` 不单独作为仓库根判据）。
5. **手册类归 `guide/` 不影响启动器呈现**：展示全由 `group` / `parent` 声明驱动
   （ADR 0093、0094），目录类别与领域圈正交。

## 后果

- 手册类教程今后立项进 `guide/`，不再挤 `subjects/`；三类判据里「学习应用」横跨
  `course` 与 `guide` 两个目录类别，按内容来源（自编大纲 vs 跟随原书）分目录，
  判据本身不变。
- gtkmm 迁移后 `workspace/` 下的 CMake 构建缓存记的是旧绝对路径，下次编译需
  reconfigure（同 ADR 0141 后果第 2 条的情形）；`workspace/` 构建产物本就不入库。
- 历史文档里「`subjects/gtkmm`」的表述（gtkmm 应用级 ADR 0001/0003、仓库级
  ADR 0131 等）是当时事实的记录，按「只增不改」不回改；现行规则以本 ADR 与各
  `AGENTS.md` 为准。
- `subjects/`→`course/` 改名落地时，本条的三分语义已就位，改名 ADR 只需处理
  牵动面（路径引用、CI、文档对账），不再议语义。
