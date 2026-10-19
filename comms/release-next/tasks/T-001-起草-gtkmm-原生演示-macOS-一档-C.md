---
id: T-001
title: 起草 gtkmm 原生演示 macOS 一档 CI 作业
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-19 15:48
updated: 2026-10-19 15:54
---
## 目标
为 `ci.yml` 起草一个 **macOS 一档的 gtkmm 原生演示检查**，对应现有的 `gtkmm-native`（Linux）与 `gtkmm-native-windows`（Windows，已在 CI 验证全绿，写法可直接参照）。草稿放 `artifacts/cursor/gtkmm-native-macos.yml`（只含这一个 job，缩进与 ci.yml 一致，可整段粘进去）。

## 要点
- runner 用 `macos-15`；依赖用 Homebrew：gtkmm4、cmake、ninja、pkg-config、gettext（`brew install` 的包名自己查实，不要凭印象——可以 `brew search`/`brew info` 在本机核对不了就在草稿里标「未核实」）。gettext 是 keg-only，要把它的 bin 加进 PATH，msgfmt 才找得到（`guide/gtkmm/scripts/check.py` 用 msgfmt）。
- 步骤与 Windows 一档对齐：checkout、pnpm、Node、装依赖、`python3 guide/gtkmm/scripts/fetch_upstream.py`、`python3 scripts/check.py gtkmm --skip-rust`。无显示器的 runner 上 `--self-check` 是否需要 xvfb 的替代，查证后写明（macOS 不需要 xvfb，但 GTK4 在无登录会话里可能起不来，这是最大不确定点，草稿里说清你的判断和依据）。
- `if:` 名单、`runs-on`、`timeout-minutes`、注释风格照 `gtkmm-native-windows`。

## 验收口径
- `actionlint` 对「把草稿并入 ci.yml 后」的文件零告警（你在临时副本里并入后跑，别改仓库里的 ci.yml）。
- 草稿开头的注释写明：哪些步骤本机无法验证、CI 首跑最可能红在哪、红了先看什么。

## 进展记录
- [2026-10-19 15:49] cursor：todo → doing
- [2026-10-19 15:53] cursor：doing → review · actionlint 临时并入副本零告警（exit=0）。草稿：comms/release-next/artifacts/cursor/gtkmm-native-macos.yml；证据：actionlint-gtkmm-native-macos.txt、T-001-evidence.md、_tmp-ci-with-macos.yml。本机无 Homebrew 未实跑；首跑风险写在草稿头（无头 Quartz/--self-check）。
- [2026-10-19 15:54] claude-code：review → done · leader 验收：草稿与 Windows 一档对齐，风险清单诚实，actionlint 零告警；已并入 ci.yml，待 CI 首跑
