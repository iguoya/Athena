# 0020 并入 Athena 仓库，作为独立应用 subjects/ascent

- 状态：已采纳
- 日期：2026-10-01
- 决策人：tiger
- 关系：取代 [0001](0001-separate-repo.md)；仓库级决定见 Athena 的 ADR 0066

## 背景

0001 把 Lumi 放在独立仓库 iguoya/English，理由是互不干扰、改动不互相影响。现在 tiger 要把
两个英语项目放进同一个仓库统一维护：Athena 的 `subjects/english`（目标考研英语二）和本应用
（目标四六级、专四、专八）。两者目标人群、考试、内容体系都不同，是并列的两个项目。

## 决策

- 本应用的代码、内容和 77 个提交的历史并入 Athena 仓库的 `subjects/ascent`（`git merge
  --allow-unrelated-histories`，历史原样保留，`git log -- subjects/ascent` 可追溯）。
- **仍是独立应用**：不引用其他应用的路径、代码或配置，依赖各拉各的，pnpm 与 Tauri 工具链
  自成一套。0001 里「不依赖 Athena 的任何代码」这一半继续成立，被取代的只是「不放进
  Athena 仓库」。
- **改名为「拾阶」· Ascent，目录与 id 用 `ascent`**（原 Lumi 英语学习）。「拾级而上」对应
  四章路线和「不按日历、按熟练度升级」的原则；名字不露考试字样，目标写在路线终点里。
  界面名、窗口标题、`app.json` 随之更新；**`productName`、`identifier`（com.iguoya.lumi）、
  Cargo 包名、`.lib` 名一律不动**：它们决定安装目录、用户数据目录和自动更新的识别，
  改了会让已安装的 Lumi 变成「另一个应用」，丢掉进度、收不到更新。
- 开发端口由 1420 改为 1440：`subjects/dsa` 已占用 1420。
- `AGENTS.md` 取代原 `CLAUDE.md` 的全部内容，`CLAUDE.md` 只导入 `AGENTS.md`（Athena ADR 0061）。
- 启动用 Athena 的 `launcher open lumi`（`app.json`）；原 `启动 Lumi（开发版）.cmd` 与
  `scripts/lumi-dev.ps1` 保留，作为 tiger 一键拉代码并运行的快捷方式。

## 与 subjects/english（磨砚）各走各的路

两个英语应用面向不同的考试和人群：本应用陪一位英语师范生读完四年（四六级、专四专八），
`subjects/english` 即「磨砚」· Whetstone 面向考研英语二。**分成两份是为了各自走出自己的路，
不是为了最后长成同一个样子**：

- 内容体系、路线、界面、教学方法、技术栈（pnpm / React / shadcn 对 npm / 原生 TS）、
  开发节奏各自演进，**不为了「保持一致」去对齐对方**。
- 对方的做法只是**参考素材**：觉得好，就按本应用的目标重新想一遍再写；不整段搬运、不把
  对方当验收标准、对方改了也不要求本应用跟着改（Athena ADR 0062、0054）。
- 两边出现相同做法时，要能说出是本应用的目标需要它，而不是因为对方有。

## 后果与未决事项

- **自动更新（0018）暂时不变**：updater 端点仍是 `iguoya/English` 的 Releases，旧仓库在
  就继续有效；旧仓库一旦归档或删除，已安装的 Lumi 会再也收不到更新。何时切换发布位置、
  切到哪里，是单独的决定。
- `.github/workflows/release.yml` 随目录并入，但 GitHub 只读仓库根的 `.github/`，它在这里
  **不会运行**。要在 Athena 仓库发布 Lumi，得把工作流迁到根并改成只对 `subjects/ascent` 生效，
  这同样留作单独决定。
- **学习应用的规范差距**：Lumi 会追踪掌握度（FSRS），按 Athena 的判据属于学习应用，但目前
  - 进度存在用户数据目录，没有 `progress/learning.db` 随仓库走（Athena ADR 0053）。侄女的
    进度该不该进版本库，需要 tiger 定。
  - 知识点没有 Athena 的难度/掌握目标两维评级与 `requires` 先修（TEACHING.md）。
  - 出处检查用 Lumi 自己的 `pnpm content:check`（条目上的 `source` id 登记在
    `content/sources.json`），尚未接入跨应用的 `content-contract.json`——两边字段模型不同，
    硬映射会失真。
