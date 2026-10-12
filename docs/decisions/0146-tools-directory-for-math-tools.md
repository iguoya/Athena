# ADR 0146：math-tools 迁入仓库根 tools/

- 日期：2026-10-12
- 状态：已接受（使用者要求：新建 `tools` 目录，把 math-tools 迁进去）
- 修订：ADR 0144 决策 3（math-tools 留在 `subjects/`）

## 背景

ADR 0144 把北极星和赛历放进 `mentor/`，math-tools 当时留在 `subjects/`：它要和
`mathematics` 在启动器里关联，还带一份 localStorage 打卡。使用者现在要一个与
`certification/`、`mentor/` 平级的 `tools/`，专门放这种配套工具。

应用 id 不改。ADR 0100 写明既有连字符名 `math-tools` 不强制改成单个单词。`math`
是这个领域里通用的说法，和课程应用 `mathematics` 也不撞名。改成 `mathematics-tools`
只是把词写全，启动命令、进程名和 localStorage 键都要跟着动，意思没有更清楚。

## 决策

1. **目录是 `tools/math-tools`。** `tools/` 与 `subjects/`、`practice/`、
   `certification/`、`mentor/` 同在仓库根。应用 id 仍是 `math-tools`，进程名
   `athena-math-tools`，端口 1451。
2. **启动器多扫这一层。** `discover_all` 再扫 `tools/*/app.json`。
   `launcher open math-tools` 不用改命令。
3. **检查、pnpm 工作区、Cargo 成员和发版矩阵跟着目录走。** 发版矩阵的 `root`
   写成 `tools`。
4. **不改 `subjects/` 这个容器名。** 顶层改名是 ADR 0145 的事，本篇只搬走
   math-tools 这一个应用。

## 后果

- ADR 0144 决策 3 不再有效。该文原文不改，索引状态栏注明由本篇修订。
- 历史 ADR 里写的 `subjects/math-tools` 是当时的路径，原文不改。现行位置以本文和
  `docs/REPOSITORY.md` 为准。
