# ADR 0147：软件设计师与嵌入式系统设计师迁入 certification

- 日期：2026-10-12
- 状态：已接受（使用者要求：把软件设计师和嵌入式系统设计师移入 `certification`）
- 关系：延续 ADR 0142（`certification/` 存放考证应用）

## 背景

`certification/` 已经放着驾考（ADR 0142）。软件设计师（`software`）和嵌入式系统设计师
（`embedded`）同样是一门应用绑定一门真实考试（ADR 0102），和驾考是同一类。它们此前
住在 `subjects/`。

## 决策

1. **目录是 `certification/software` 与 `certification/embedded`。** id、进程名
   （`athena-software`、`athena-embedded`）、知识点前缀（`sc.`、`esd.`）、端口、
   `group`、进度库全部不动。
2. **实践子课程不跟着搬。** `database`、`firmware`、`microcontroller`、`rtos` 仍在
   `subjects/`。`os`、`network` 的本体仍归 cs408。`app.json` 里的 `parent` 仍是
   应用 id，不写路径。
3. **启动器不用加新的扫描层。** `discover_all` 已经扫 `certification/`。
   `launcher open software` 与 `launcher open embedded` 命令不变。
4. **检查、pnpm 工作区与 Cargo 成员跟着目录走。** 工作区只收这两个 Tauri 应用，
   不把 Flutter 的 `driver` 收进去。

## 后果

- 历史 ADR 里写的 `subjects/software`、`subjects/embedded` 是当时的路径，原文不改。
  现行位置以本文和 `docs/REPOSITORY.md` 为准。
- 不改 `subjects/` 这个容器名（ADR 0145）。
