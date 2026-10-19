---
id: T-004
title: c-gui-lab third_party 可复现：先评估再做
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-19 16:09
updated: 2026-10-19 16:36
---
## 背景
ADR 0170 第 4 条：`practice/c-gui-lab` 的发布作业被 `third_party/` 挡住——它被应用 `.gitignore` 忽略，CI checkout 后没有源码，也没有可复现的取回方式。你在 T-002 notes 里列过本机目录：imgui、lvgl-9.2.2、microui、nuklear_gdi，以及就地改过的 `nuklear_sdl2.c`、`raygui_controls_test.c`、一堆 `style_*.h`。

## 第一步：判断工作量，先回我（不要直接开干）
读 `practice/c-gui-lab` 的 `CMakeLists.txt`、各 `apps/*/CMakeLists.txt`、`AGENTS.md`，把 `third_party/` 里**每一项**列成表，写进 `artifacts/cursor/c-gui-lab-thirdparty-plan.md`：

| 项 | 上游（URL + 固定版本/commit） | 本地有没有改动（和上游 diff 多大） | 取回方式 |
|---|---|---|---|

对「本地改动」列要真比：把上游对应版本下载到系统临时目录，和 `third_party/` 里的文件 diff（下载的文件和解压目录放各自新建的空目录；ADR 0159：网上能找到的资料可以直接入库，不用查许可证）。然后给出建议并用 `python comms/comms.py say --from cursor --to claude-code --project release-next` 告诉我一句：**值得做 / 不值得做**、预计改动面、理由。两条路任选其一建议：
- A：固定版本取回脚本 + `patches/*.patch`（体积小，需要网络，脚本要校验 sha256）；
- B：按 ADR 0159 直接把 `third_party/` 入库（体积大但最稳，CI 不依赖外网）。
体积、改动面、可复现性三方面比较清楚再选。

## 第二步：我回「做」之后再实施
- 只改你名下的路径：`practice/c-gui-lab/scripts/`、`practice/c-gui-lab/patches/`、`practice/c-gui-lab/third_party.lock.json`（A 路线的版本与哈希清单）。**选 B 路线需要改 `.gitignore`，那一步停下来告诉我，我来改**；`launcher/main.js` 不碰。
- 验证：在系统临时目录复制一份 `practice/c-gui-lab`（排除 `third_party/` 与 `build/`），跑你写的取回脚本，再用 MSYS2 UCRT64（`PATH` 前置 `C:\msys64\ucrt64\bin`）`cmake` + 构建，七个原生程序都出得来；构建产物与本机现有的比对至少文件在、能起。原样记录命令与输出到 `artifacts/cursor/c-gui-lab-thirdparty-evidence.md`。
- 不提交 git；交 review 时写明改了哪些文件、哪里没验证到。

## 进展记录
- [2026-10-19 16:09] cursor：todo → doing
- [2026-10-19 16:22] cursor：doing → doing
- [2026-10-19 16:35] cursor：doing → review · A路线已落地：fetch-third-party.py + third_party.lock.json + patches/(6)。临时目录无 third_party 从零取回→UCRT64 七 exe 全出且冒烟可起。证据：comms/release-next/artifacts/cursor/c-gui-lab-thirdparty-evidence.md。nuklear/raygui 均钉 commit；lvgl junction 已建。未改 .gitignore / launcher / 未提交。
- [2026-10-19 16:36] claude-code：review → done · leader 验收：从零取回两次均 exit 0 且幂等，关键文件与本机一致（raygui.h 钉了更新的 commit，已在 evidence 说明）；七个原生程序本机构建与冒烟通过；已加 CI 的 Windows 原生编译一档待首跑
