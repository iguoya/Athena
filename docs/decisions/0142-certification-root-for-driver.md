# ADR 0142：驾考放到仓库根的 certification

- 日期：2026-10-12
- 状态：已接受（使用者要求：新建 `certification` 目录，与 `exercise` 平级，存放驾考应用）

## 背景

驾考应用在 `subjects/driver`。使用者要一个与仓库根 `exercise/` 平级的 `certification/`，用来放这门考证应用。应用 id 仍是 `driver`，知识点前缀仍是 `drive.`。

## 决策

1. **目录是 `certification/driver`。** `certification/` 与 `exercise/`、`subjects/`、`practice/` 同在仓库根。应用本身仍叫 `driver`，不改 id、不改进程名 `athena-driver`。
2. **启动器多扫这一层。** `discover_all` 在 `subjects/`、`practice/` 之后再扫 `certification/*/app.json`。`launcher open driver` 不用改命令。
3. **检查与发版跟着目录走。** 根 `scripts/check.py` 的应用根包含 `certification`。发布工作流里的驾考路径改为 `certification/driver`。

## 后果

- 历史 ADR 里写的 `subjects/driver` 是当时的路径，原文不改。现行位置以本文和 `docs/REPOSITORY.md` 为准。
- `exercise/` 仍是仓库根上的空目录，本决定不给它登记用途。
