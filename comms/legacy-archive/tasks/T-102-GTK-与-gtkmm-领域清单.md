---
id: T-102
title: GTK 与 gtkmm 领域清单
owner: cursor
status: done
priority: P1
depends: 
created: 2026-10-21 15:26
updated: 2026-10-21 16:00
---
## 目标
为 **GTK（C）** 与 **gtkmm（C++）** 出清单：`manifest-gtk.json/.md`（目标 `practice/c-gui-lab`）与 `manifest-gtkmm.json/.md`（目标 **新建应用** `programming/gtkmm-lab`，与现有 `guide/gtkmm` 官方手册精读应用互不引用，ADR 0176）。

## 范围（全部在 `.cache/legacy-src/` 下）
- `Linux/GTK/`（约 1635 个文件，目录如 `GtkApp`、`g17-anjuta`、`g19-basicwindow`、`g20-box`、`g32-grid`、`25-glade`…；**怀疑含大量重复的 anjuta/glade 生成样板与第三方文件，核实**）
- `Linux/GTKMM/`、`Linux/Examples_Gtkmm/`、`Linux/gtkmm-application-template/`
- 看一眼 `practice/c-gui-lab`（`apps/`、`AGENTS.md`）了解它现在放什么，给出历史 GTK 条目应放哪个位置的建议（它是 Electron 母体启动的 GTK4/ImGui/LVGL 演示集，GTK 旧代码是 GTK2/3 时代还是 GTK4，决定能否并入、是否要标 `read-only`）。
- 看一眼 `guide/gtkmm` 现有内容范围，确保 `gtkmm-lab` 的条目不与它重叠（它是官方教程翻译；旧练习是使用者自己的）。

## 特别要求
- Anjuta/Glade 工程生成的样板（`configure.ac`、`Makefile.in`、`autogen.sh`、`po/` 等）是生成物，`drop-junk`，但要在 md 里统计数量。
- 区分 GTK 版本（2/3/4）与 gtkmm 版本（2.4/3.0/4.0）——影响能否在现代环境运行。本机是 Windows，没有 GTK 开发库：一律标 `toolchain` 或 `read-only`，**不要试图安装**；能静态判断的（头文件、API 名）就静态判断并写进 quality_notes。

## 第一阶段只做清单（只读）
格式、字段、零遗漏要求见 `comms/legacy-archive/README.md`「清单格式」；决策依据见 ADR 0176（先读）。源码在 `.cache/legacy-src/`，**只读**。
产出只写进你的 `comms/legacy-archive/artifacts/<你的名字>/`，不改仓库其他地方、不提交 git。

## 通用做法
1. 先 `git -C .cache/legacy-src/<仓库> ls-files` 列出被跟踪文件，按目录划分“历史练习单元”（一个模式/一个数据结构/一个小工程为一个单元），不要一个文件一条。
2. 对所有疑似重复的单元做内容哈希比对（忽略行尾 CRLF/LF 与首尾空白），确定规范版（取最新最完整）。
3. 第三方判定要有依据（上游库名/URL、文件头版权声明、与官方包比对），不是你自己写的就 `drop-third-party`，不要入库。
4. 对 `run: cli` 的规范版在本机（Windows，MinGW g++ 或 MSVC 可用）真编译真运行，记录命令和输出首行；编译失败写原因（缺头文件/平台相关/语法过旧等），不要凭印象。需要 Qt/GTK/SDL 的标 `toolchain`，Linux 专有标 `linux-only`，不要试图装库。
5. `quality_notes` 写后续批注要抓的真问题，具体到文件/类（如“Singleton 用裸指针且无释放”“main.cpp 里 new 后从不 delete”“头文件缺 include guard”），不写套话。
6. 写完用小脚本校验：你负责范围内每个被跟踪的文件是否都被单元覆盖或 drop；脚本和输出放 `verify-<领域>.txt`。
7. 做完把任务转 review，`--note` 里写：单元数、keep/drop 各多少、覆盖校验结果、编译实测通过/失败数、manifest 路径。有拿不准的归属或争议项写进 md 的“待裁决”并发消息给 claude-code，不要自作主张。

## 进展记录
- [2026-10-21 15:44] cursor：todo → doing
- [2026-10-21 15:49] cursor：doing → review · GTK: 单元127 keep80 drop-junk47（生成物575文件）覆盖1635/0遗漏；gtkmm: 单元15 keep7 drop-junk8 覆盖192/0遗漏；Windows未装GTK未编译（build_checked全false）。证据：artifacts/cursor/manifest-gtk.json|.md、manifest-gtkmm.json|.md、verify-gtk.txt、verify-gtkmm.txt、note-c-gui-lab-placement.md。待裁决已私信。
- [2026-10-21 16:00] claude-code：review → done · leader 验收：摘要与零遗漏校验、编译证据已核对；两项 leader 裁决见消息
