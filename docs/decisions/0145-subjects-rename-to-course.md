# ADR 0145：subjects/ 改名 course/

- 日期：2026-10-12
- 状态：已接受（使用者要求：「将 subjects 改名 course，更符合里面应用的定位」）
- 草拟：[STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V5（ADR 0134 流程，
  落 ADR 前已复看草稿）
- 关系：落实 [ADR 0143](0143-guide-directory.md) 决策 2 预留的改名；与 ADR 0142
  （certification）、ADR 0144（reference）同属顶层分类重组

## 背景

ADR 0143 定了顶层语义三分并把 `course` 定为课程类的目标名，改名动作留待另行 ADR。
ADR 0142（certification）与 ADR 0144（reference）落地后，考证类与图谱/参考类陆续
迁出 `subjects/`，gtkmm 也已定迁 `guide/`——`subjects/` 里剩下的**全部是课程类
学习应用**（自编教学设计：大纲→过程→实验三层）。目录名「学科」与内容的偏差至此
消失，改名的时机成熟。

ADR 0134 要求「`id` 与目录名一经入库不改名」；本条改的是**顶层容器名**，不是任何
应用自己的 `id` 与目录名（后者全部不动），但按同样的纪律走新 ADR 并按牵动面清单
一次改齐。

## 决策

1. **`subjects/` 整体改名为 `course/`**，`git mv` 保留 rename 历史。改名后
   `course/` 装课程类学习应用，与 `guide/`（手册类）、`practice/`（项目类）、
   `certification/`（考证类）、`reference/`（图谱/参考类）平级。
2. **应用层面零改动**：所有应用的 id、目录名、进程名 `athena-<id>`、知识点前缀、
   `progress/learning.db`、`app.json` 全部不变；`launcher open <id>` 命令不变。
3. **牵动面一次改齐**（清单见 STRUCTURE-PROPOSALS V5）：启动器 `manifest.rs` 的
   `discover()` 与 `paths.rs` 仓库根识别锚、根 `scripts/check.py`（`APP_ROOTS` 与
   各处对账）、`ci.yml` / `release.yml` 的 working-directory 与产物路径、
   `pnpm-workspace.yaml` 与根 `Cargo.toml` 的成员路径、三处文档登记
   （REPOSITORY.md、根 README、根 AGENTS.md）、各应用自述里的 `subjects/<id>`
   路径批量替换。
4. **不改**：历史 ADR 原文（`subjects/<id>` 是当时的事实）、STRUCTURE-PROPOSALS
   历史节、`archive/`、进度库、知识点前缀。
5. **执行时机**：并行重组会话在 `subjects/` 上的未提交改动落库后执行；届时与
   gtkmm→`guide/` 迁移（ADR 0143）一批完成，再放行 ADR 0144 的 reference 迁移。

## 后果

- 顶层目录名与应用类别一一对应，新增应用先选类别再进目录，不再有「目录说学科、
  装的不全是学科」的偏差。
- 本地脚本、笔记里写死的 `subjects/…` 路径失效；以 `launcher open <id>` 为入口
  的使用不受影响。
- 历史 ADR 与旧文档里的 `subjects/<id>` 不回改，现行位置以本文与
  `docs/REPOSITORY.md` 为准。
