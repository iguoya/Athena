---
id: T-002
title: 起草 c-gui-lab（Electron）发布打包作业
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-19 15:48
updated: 2026-10-19 16:02
---
## 目标
`practice/c-gui-lab`（Electron，`package.json` 入口 `launcher/main.js`，`apps/` 下有原生 C 小程序）要按 ADR 0168 进发布。起草**它进 `release.yml` 的打包作业**，放 `artifacts/cursor/c-gui-lab-release.yml`（一个 job，可整段粘进 release.yml），并先弄清三件事，写进 `artifacts/cursor/c-gui-lab-notes.md`：

1. 这个应用现在**怎么在本机跑起来**（`launcher/main.js` 做了什么、`apps/` 的 C 程序是谁编译的、安装包里要不要带编译产物）。照 `AGENTS.md`、`README.md` 与源码读，不凭印象。
2. 选 electron-builder 还是 @electron/packager + 各平台打包工具，理由；产物形态要与现有 Tauri 矩阵一致（Windows NSIS、macOS DMG、Linux DEB），`mainBinaryName` 风格 `athena-c-gui-lab`（ADR 0168 第 4 条）。
3. 原生 C 部分（CMake / `third_party`）能不能在三个 runner 上无头编出来；不能的平台，诚实写「该平台不进包」并给理由（ADR 0049：成本过高的可以排除，但要写明）。

## 验收口径
- 草稿 job 的 `actionlint` 在「并入 release.yml 的临时副本」里零告警；产物命名要能被 release.yml 末尾的 `publish` 作业收集（读 release.yml 的收集与改名逻辑，照着对，别只看 tauri-apps 作业）。
- notes 里列出「只能在 CI 上验证的步骤」和最可能红的三处。

## 进展记录
- [2026-10-19 15:49] cursor：todo → doing
- [2026-10-19 15:54] cursor：doing → review · actionlint 临时合并副本零告警（EXIT=0）。交付：artifacts/cursor/c-gui-lab-release.yml（windows-only NSIS，electron-builder，产物 athena-c-gui-lab-<ver>-windows-x64-setup.exe）、c-gui-lab-notes.md（启动方式/选型/三平台诚实排除/CI-only步骤/最可能红三处）、证据 actionlint-c-gui-lab.out.txt + _release-with-c-gui-lab.yml（publish.needs 已示意加 c-gui-lab）。未改 .github/、未提交。
- [2026-10-19 16:02] claude-code：review → done · leader 验收：调研与草稿属实、actionlint 零告警；按 ADR 0170 第 3、4 条不集成，草稿存档
