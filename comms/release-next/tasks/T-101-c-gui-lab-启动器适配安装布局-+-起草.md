---
id: T-101
title: c-gui-lab 启动器适配安装布局 + 起草安装包 CI 作业
owner: zcode
status: done
priority: P1
depends: 
created: 2026-10-20 07:51
updated: 2026-10-20 08:56
---
## 背景
`practice/c-gui-lab`（Electron 母体 + 七个 Win32/MSYS2 原生程序）要出 Windows 安装包（ADR 0170 第 4 条）。已经完成的前置：`third_party/` 可复现（`scripts/fetch-third-party.py` 等），CI 的 `c-gui-lab-native` 一档首跑全绿。**还剩两件事，归你做**：

1. **`launcher/main.js` 适配安装布局**。现在 `PROJECT_ROOT = path.join(__dirname, "..")`，各程序路径写死 `build/apps/<名>/<名>.exe`，`MSYS2_BIN = "C:\msys64\ucrt64\bin"` 写死。要求：
   - 开发树（`npm start`）行为**完全不变**；
   - 打进 electron-builder 的 asar / 安装目录之后，能找到旁路放着的原生程序（`asarUnpack` 或 `extraResources`，选哪个你判断，写理由），exe 不能从 asar 里 spawn；
   - 打包后不依赖 `C:\msys64`：原生程序所需的 MinGW 运行库 DLL 放在各 exe 旁边（由打包作业收集），`childEnv()` 在打包态不再往 PATH 塞 MSYS2 目录，`OFFICIAL`（官方 gtk4-demo 等）探测不到就灰掉入口，现有降级逻辑保留；
   - `--selftest` 在两种布局下都要能跑，打包态的自检至少验证「七个 exe 都在、都能 spawn 起来」。
2. **起草一个能在 `ci.yml` 里验证的 Windows 安装包作业**（草稿放 `artifacts/zcode/c-gui-lab-package-ci.yml`，一个 job，我负责并入 ci.yml 并触发）：在已通过的 `c-gui-lab-native` 之后——取回 third_party、编七个程序、收集 DLL、用 electron-builder 出 NSIS 安装包、**再静默安装到临时目录并运行 `--selftest`**（这是「装得出、跑得起」的真验证）。起点是 Cursor 的草稿 `comms/release-next/artifacts/cursor/c-gui-lab-release.yml` 与 `c-gui-lab-notes.md`（有 DLL 用 ntldd 收集的做法、electron-builder 配置、产物命名 `athena-c-gui-lab-<ver>-windows-x64-setup.exe`），但它的 third_party 那一步要换成 fetch 脚本，并且**别照抄**：自己判断哪些写法在 runner 上站得住。

## 你名下的路径
`practice/c-gui-lab/launcher/`、`practice/c-gui-lab/package.json`、`practice/c-gui-lab/electron-builder.yml`（新建的话）、`comms/release-next/artifacts/zcode/`。其余（`.github/`、`apps/`、`CMakeLists.txt`、`scripts/`、`patches/`）不动；需要改请发消息给我。

## 验收口径
- `npm start` 路径本机冒烟通过（`node_modules` 在应用目录，没有就 `npm ci`）；`--selftest` 开发树布局通过。
- 打包态布局你在本机能模拟到什么程度就模拟（例如手工建一个 `resources/` 结构），做不到的写进交付说明，列出「只能在 CI 验证」的步骤和最可能红的三处。
- actionlint 对「并入 ci.yml 的临时副本」零告警。
- 做完 `status review`，附证据路径。不提交 git。

## 进展记录
- [2026-10-20 07:54] zcode：todo → doing
- [2026-10-20 08:17] zcode：doing → review · 两件交付齐：1) launcher/main.js 适配安装布局——NATIVE_ROOT 按 app.isPackaged 二分，原生程序走 extraResources 放 resources/native（选型理由见交付说明），打包态 childEnv 不再塞 MSYS2 PATH，selftest 统一为七个 exe 逐个 spawn-存活-杀；2) 安装包 CI 作业草稿 artifacts/zcode/c-gui-lab-package-ci.yml（third_party 用 fetch 脚本、ntldd 收 DLL 后当场复查无 not found、NSIS 静默安装+安装态 selftest）。本机证据（artifacts/zcode/T-101/ 目录）：开发树 selftest 七个全活 exit 0；npm start 冒烟截图 UI 正常；electron-builder --dir 产物在滤净 MSYS2 的 PATH 下打包态 selftest 七个全活 exit 0；actionlint+shellcheck 对并入 ci.yml 副本零告警；应用 check.py 全绿。package-lock.json 已更新须与 main.js/electron-builder.yml 同提交。未提交 git。详见 VERIFICATION.md。
- [2026-10-20 08:56] claude-code：review → done · leader 验收：ci.yml 安装包一档首次完整通过（run 39349483787，安装态 selftest 七个原生程序都起得来）；我补了三处 CI 步骤的坑（Git Bash PATH、系统组件 DLL 误报、GUI 程序 Start-Process -Wait），已并入 release.yml
