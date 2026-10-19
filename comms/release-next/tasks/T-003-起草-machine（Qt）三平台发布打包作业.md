---
id: T-003
title: 起草 machine（Qt）三平台发布打包作业
owner: cursor
status: done
priority: P2
depends: 
created: 2026-10-19 15:48
updated: 2026-10-19 16:02
---
## 目标
`programming/machine`（Qt Quick / QML，`CMakeLists.txt`，已有 `packaging/windows/app.rc.in`，`app.json` 里写了 Qt 6.8.1 路径）要按 ADR 0168 进发布。起草它的**三平台打包作业**，放 `artifacts/cursor/machine-release.yml`，并把调研写进 `artifacts/cursor/machine-notes.md`：

- Qt 在 CI 上怎么装（`jurplel/install-qt-action` 的版本、模块、与本机 6.8.1 对齐）；`ci.yml` 里已有 `qt-quick` / `qt-quick-windows` 两个验证作业，**照它们已经验证过的装法**，别另起炉灶（读 ci.yml 里那两个 job）。
- 打包：Windows 用 `windeployqt` + NSIS（或与现有 Tauri 的 NSIS 产物形态一致的做法）、macOS 用 `macdeployqt` 出 DMG、Linux 出 DEB。`mainBinaryName` 用 `athena-machine`。
- 课程内容（`content/`、`qml/`、`labs/`）是否要进包、运行时怎么找到它；`ATHENA_*_ROOT` 之类环境变量的现有约定见 `programming/machine/AGENTS.md`，别破坏。
- 做不到的平台诚实排除并写理由。

## 验收口径
同 T-002：actionlint 零告警（在临时副本里并入 release.yml 后），产物命名能被 `publish` 作业收集，notes 里列出只能在 CI 验证的步骤与最可能红的三处。这一项比 T-002 难，做不完的部分写清楚停在哪，不要硬凑。

## 进展记录
- [2026-10-19 15:48] cursor：todo → doing
- [2026-10-19 15:57] cursor：doing → review · actionlint 临时并入 release.yml（含 publish.needs+=machine）零告警 exit=0。交付：artifacts/cursor/machine-release.yml（Win NSIS / macOS arm64 DMG / Linux DEB；跟 ci.yml 装 Qt）、machine-notes.md（ATHENA_MACHINE_ROOT、jurplel 不用、macos-x86_64 排除、CI-only 与最可能红三处）。证据：machine-actionlint.out.txt、_release-with-machine.yml、_run_actionlint.py。未改 .github/、未提交。
- [2026-10-19 16:02] claude-code：review → done · leader 验收：调研与草稿属实、actionlint 零告警；按 ADR 0170 第 3、4 条不集成，草稿存档
