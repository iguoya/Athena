# ADR 0144：新增顶层目录 reference/（图谱/参考类），北极星、math-tools、competitions 迁入

- 日期：2026-10-12
- 状态：已接受（使用者 2026-10-12：目录名 `reference` 定稿，math-tools 同批并入，等相邻迁移
  落地后再执行；草拟见 [STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V4，ADR 0134 流程）
- 执行状态：**未执行**，本篇只定决定，迁移排在 0142、0143 与 `subjects/`→`course/` 之后
- 关系：延续 ADR 0142（certification）、0143（guide）的顶层分类思路；ADR 0084、0114 把 math-tools、
  competitions 归入图谱/参考类，本篇把这个归类落到目录

## 背景

`docs/REPOSITORY.md` 的三类判据把应用分成学习应用、图谱/参考类、素材坑。学习应用已按内容来源
分到 `subjects/`（自编教学设计，ADR 0143 起称 `course`）、`guide/`（跟随外部手册）、
`practice/`（做出能跑的东西）。图谱/参考类却一直留在 `subjects/`，当前有三个成员：

- `polaris`（北极星）：技术体系的路线图与指南针，不教课，不建进度库。
- `math-tools`：数学学习的配套工具（练习纲要、矩阵实验室、函数绘图），ADR 0084 明确归图谱/参考类。
- `competitions`（赛历）：竞赛清单供查阅与决策，ADR 0114 明确归图谱/参考类。

三者共同点：只呈现信息或提供工具供查阅使用，不要求学习者被教会什么，也不证明学习者进步了，
所以教学规范、出处分档、进度库都不适用。把它们和自编课程放在同一个目录里，目录名说的是
「学科」，实际装的却是另一类东西。

## 决策

1. **新增顶层目录 `reference/`：图谱/参考类应用。** 与 `subjects/`、`guide/`、`practice/`、
   `certification/` 平级，一个应用一个子目录。定义：呈现信息或提供工具供查阅使用，不判分、
   不建进度库，跨应用教学规范不生效（即「三类判据」中的图谱/参考类）。目录类别与判据类别
   对应；应用的类别变了（如 math-tools 升级成带掌握度的学习应用），目录随之迁走，且先立 ADR。
2. **`polaris`、`math-tools`、`competitions` 迁入，纯目录搬家。** id、进程名（`athena-<id>`）、
   端口、`group`（图谱 / 数学 / 大赛）、`parent`、内容、`lifecycle` 全部不变；领域圈由 `app.json`
   声明驱动（ADR 0093、0094），与目录类别正交，启动器呈现不变。
3. **名字用 `reference`。** 对应仓库自己的判据措辞「图谱/参考类」，并且覆盖图谱、清单、工具
   三种形态。`atlas` 装不下赛历与矩阵实验室，`toolkit` 装不下北极星，故不用。
   与 `polaris/content/sources/reference/` 重名但层级不同，无冲突。
4. **启动器与统一检查把 `reference/` 当一个应用根。** `launcher/core` 发现清单、`scripts/check.py`
   的 `APP_ROOTS` 与根白名单同步，机制与 `guide/`、`certification/` 一致。
5. **共享构建配置同步改。** `pnpm-workspace.yaml` 的 `packages` 补 `reference/*`（否则三个应用被
   静默踢出同栈工作区）；根 `Cargo.toml` 的 `members` 三条路径改为 `reference/<id>/src-tauri`；
   `ci.yml`、`release.yml` 的 working-directory 与产物路径同步。目录深度不变，相对路径
   `../../packages/*` 不受影响。
6. **执行时机：等相邻迁移落地之后。** 0142、0143 的迁移与 `subjects/`→`course/` 改名都触及
   启动器、`check.py`、两个 workflow，且工作区里有并行会话的未提交改动。本篇的迁移排在它们之后
   单独一次提交，不与它们混改同一批文件（AGENTS.md「多个代理并行」）。

## 后果

- 图谱/参考类有了自己的目录，`subjects/`（将来的 `course/`）只装自编教学设计的课程。
- 历史 ADR 与各应用 ADR 里的 `subjects/polaris`、`subjects/math-tools`、`subjects/competitions`
  是当时事实的记录，按「只增不改」不回改；现行路径以本篇与 `docs/REPOSITORY.md` 为准。
  `subjects/algorithms`、`data-structures`、`linux`、`mathematics` 的 `AGENTS.md` 里有指向
  这三个应用的路径文字，迁移时同步。
- 登记三处：`docs/REPOSITORY.md`（结构树、名字对照表、三类判据）、根 `README.md`、根 `AGENTS.md`。
- `docs/decisions/README.md` 的索引行待补；该文件当前有他人的未提交改动（0141、0142 行），
  本篇不碰，由负责索引的一方或执行迁移时一并补。
- 此后新增图谱/参考类应用直接进 `reference/`；素材坑没有 `app.json`，不属于任何应用根，不受影响。
- 风险：math-tools 带一份 localStorage 打卡清单，边界最接近学习应用；其 AGENTS.md 已写明升级
  需先立 ADR，届时按决策 1 迁出。
