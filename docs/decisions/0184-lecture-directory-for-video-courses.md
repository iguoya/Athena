# ADR 0184：视频课应用单独成 `lecture/` 目录

- 日期：2026-10-23
- 状态：已接受（使用者指示：「将这类关联视频教程的应用单独放 lecture 文件夹目录」）
- 关系：沿 [ADR 0182](0182-weng-c-programming.md)（课堂工作台）与 [ADR 0180](0180-chen-linear-algebra-mooc.md)（西电慕课）；
  目录归类判据见 [ADR 0060](0060-subjects-and-practice.md)、[ADR 0143](0143-guide-directory.md)；应用 `id` 不变（`id` 不改嫁，见根 AGENTS.md）

## 背景

视频课原来都挂在 `guide/`（手册类：跟随一本外部手册精读）。但视频课与手册类的骨架不同：界面里有播放窗格（或外链），
内容单位是「集 / 节拍 / 任务」而不是书的章节，题源出处挂在「分集号 + 时间」而不是页码，还有自己的播放桥、字幕/转写底本和 comms 舱（`video-course`）。
现在要为自考「高等数学（工本）」「线性代数（工）」各做一个视频课应用，视频课将有四个，继续混在 `guide/` 里已经分不清。

## 决策

1. **新增顶层目录 `lecture/<id>/`**，装「以一套外部视频课为底本、视频是界面一部分」的学习应用。判据：底本是视频课（有集数与时间锚点），不是书或手册。
   书/手册精读仍归 `guide/`，视频课里讲什么科目由 `app.json` 的 `group`（「数学」「程序设计」圈）决定，目录只表达**形态**。
2. **迁入现有两个**：`guide/weng-c-programming` → `lecture/weng-c-programming`，`guide/chen-linear-algebra-mooc` → `lecture/chen-linear-algebra-mooc`。
   `id`、进程名、知识点前缀、端口、用户数据目录、进度库**一概不变**，已有进度不受影响；`git mv` 保留历史。
3. **新建两个**（视频底本待 comms 舱 T-005 调研后由使用者选定，选定后各自在 `lecture/` 下建，名字随之定，本 ADR 不预占）：自考高等数学（工本）、自考线性代数（工）。
   与 `self-study/` 里同科目的文本应用并存、互不引用，知识点前缀独立。
4. **登记面**：启动器 `discover_all` 增加 `lecture/`（与 `guide/` 同层，不进 `LEARNING_ROOTS`，所以不改界面分组）；`scripts/check.py` 的 `APP_ROOTS`、
   pnpm 工作区、根 Cargo 工作区成员、`release_readiness.py` 的目录清单、`REPOSITORY.md`、根 `README.md`、根 `AGENTS.md` 结构树同步。
5. **播放桥先复制不抽共用件**（沿 ADR 0182 决策 10、[ADR 0132](0132-defer-shared-layer.md)）：新建的两个应用复制翁恺应用的壳，稳定后再评估抽到 `packages/`。
6. **历史 ADR 与 comms 记录里的旧路径不改**（ADR 只增不改；comms 是流水）。读到 `guide/weng-c-programming` 等旧路径时按本 ADR 对照。

## 后果

- 迁移是纯移动加登记，不改应用行为；各应用 `AGENTS.md` 里的自述路径随迁移更新。
- 已装的 `node_modules`、`target` 缓存随目录移动；pnpm 锁文件的 importer 键改路径后需要重装一次链接。
- 之后凡「按视频课学」的新应用先放 `lecture/`，不再放 `guide/`。
