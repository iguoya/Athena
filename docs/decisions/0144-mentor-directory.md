# ADR 0144：新增顶层目录 mentor/（导师类），北极星、赛历迁入

- 日期：2026-10-12
- 状态：已接受并已执行（使用者 2026-10-12：目录名用 `mentor`，把北极星与大赛应用迁进去；
  草拟见 [STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V4，ADR 0134 流程）
- 修订：本篇首版（e6ae91ce）定名 `reference/`、三个应用并入；执行前使用者改为 `mentor/`、
  只迁北极星与赛历，math-tools 留 `subjects/`。首版未执行过，按 ADR 0134 决策 4 直接修订，
  文件名随之由 `0144-reference-directory.md` 改为本名
- 关系：延续 ADR 0142（certification）、0143（guide）的顶层分类思路；ADR 0114 把赛历归入
  图谱/参考类，北极星自述同类，本篇把这个归类落到目录

## 背景

`docs/REPOSITORY.md` 的三类判据把应用分成学习应用、图谱/参考类、素材坑。学习应用已按内容来源
分到 `subjects/`（自编教学设计，ADR 0143 起称 `course`）、`guide/`（跟随外部手册）、
`practice/`（做出能跑的东西）。图谱/参考类却一直留在 `subjects/`：

- `polaris`（北极星）：技术体系的路线图与指南针，让人先看见全局、主次和去向，再决定进哪个
  应用练细节。不教课，不建进度库。
- `competitions`（赛历）：竞赛清单供查阅与决策——谁能参加、什么方向、和哪门课对得上。
  不判分，不建进度库。

两者共同点：给人**方向和决策依据**，不要求学习者被教会什么，也不证明学习者进步了，所以教学
规范、出处分档、进度库都不适用。放在自编课程的目录里，目录名说的是「学科」，装的却是另一类东西。

## 决策

1. **新增顶层目录 `mentor/`：导师类（即三类判据中的图谱/参考类）应用。** 与 `subjects/`、
   `guide/`、`practice/`、`certification/` 平级，一个应用一个子目录。定义：为学习者指路、
   提供查阅与决策依据，不教课、不判分、不建进度库，跨应用教学规范不生效。应用的类别变了
   （例如升级成带掌握度的学习应用），目录随之迁走，且先立 ADR。
2. **`polaris`、`competitions` 迁入，纯目录搬家。** id、进程名（`athena-<id>`）、端口、
   `group`（图谱 / 大赛）、`parent`、内容、`lifecycle` 全部不变；领域圈由 `app.json` 声明
   驱动（ADR 0093、0094），与目录类别正交，启动器呈现不变。
3. **`math-tools` 不迁，留在 `subjects/`。** 它是数学学习的配套工具，要在启动器里与
   `mathematics` 关联（ADR 0084 当时的归属理由），且带一份 localStorage 打卡清单，边界最
   接近学习应用。将来若数学两个应用整体换位置，另议。
4. **名字用 `mentor`（导师）。** 北极星的定位就是路线图与指南针，赛历是替人挑赛事，两者
   做的都是「给方向」而不是「教内容」。落选的候选：`reference`（只描述形态，不描述作用）、
   `atlas`（装不下赛历）、`guidance`（与 `guide/` 太像易混）、`support`（过泛）。
5. **启动器与统一检查把 `mentor/` 当一个应用根。** `launcher/core` 发现清单追加一层，
   `scripts/check.py` 的 `APP_ROOTS`、根白名单、结构树、README 与名字表对账、React 前端检查
   同步覆盖 `mentor/`。
6. **发版矩阵加 `root` 字段。** `release.yml` 的 working-directory 与产物路径写成
   `${{ matrix.root || 'subjects' }}/${{ matrix.app }}`，北极星的四个矩阵项写 `root: mentor`。
7. **共享构建配置跟着改。** 根 `pnpm-workspace.yaml` 的 `packages` 补 `mentor/*`，根
   `Cargo.toml` 的 `members` 里两条路径改为 `mentor/<id>/src-tauri`。这两份文件当时是并行会话
   尚未入库的新文件，本次只改工作区里的这两处，随它们的所属会话一并提交。目录深度不变
   （`mentor/<id>` 与 `subjects/<id>` 同为两层），相对路径不受影响。

## 后果

- 图谱/参考类有了自己的目录，`subjects/`（将来的 `course/`）里只剩自编教学设计的课程与
  math-tools 这一个有理由的例外。
- 历史 ADR 与各应用 ADR 里的 `subjects/polaris`、`subjects/competitions` 是当时事实的记录，
  按「只增不改」不回改；现行路径以本篇与 `docs/REPOSITORY.md` 为准。
- 登记三处已同步：`docs/REPOSITORY.md`（结构树、三类判据）、根 `README.md`、根 `AGENTS.md`；
  `subjects/algorithms|data-structures|linux|mathematics` 与两个应用自己的文档里的路径同步更新。
- 此后新增图谱/参考类应用进 `mentor/`；素材坑没有 `app.json`，不属于任何应用根，不受影响。
- ADR 0145（`subjects/`→`course/`）写的是 `reference/`，应读作本篇的 `mentor/`；其牵动面清单
  新增一项：`course/` 改名时 `launcher/core` 的发现清单与 `check.py` 里已有 `mentor`，无需重复处理。
