---
id: T-101
title: Qt 领域清单（Qt5、Linux/QT、PyQt、QML、Sample）
owner: cursor
status: done
priority: P0
depends: 
created: 2026-10-21 15:26
updated: 2026-10-21 16:00
---
## 目标
为 **Qt** 领域出清单 `manifest-qt.json/.md`，目标 **新建应用** `programming/qt`（ADR 0176）。

## 范围（全部在 `.cache/legacy-src/` 下）
- `Qt5/` 整个仓库（约 240 个 cpp、192 个 bmp、142 个 .pro、93 个 qml、84 个 ui；编号目录如 `01-SignalSlot`、`14-Quick`、`20-Layout` 等）
- `Linux/QT/`（含 `QtApp/` 约 519 个文件）、`Linux/PyQt/`、`Linux/QML/`、`Linux/Sample/`（`chap01…chap15`，疑似某本 Qt 教材的随书样例，请核实：是否整套拷贝？有没有使用者自己的改动？）
- `Practice/QT/`、`Practice/untitled/`（Qt Creator 默认工程名，判断内容）、`Practice/CGI/` 若与 Qt 无关则不归你

## 特别要求
- `Qt5/` 与 `Linux/QT/` 里大量编号目录（`11-HelloWorld`、`13-EmbedWidget`、`20-SignalAndSlot`…）疑似同一批练习的两份拷贝，**先哈希去重**。
- 按主题聚类：基础信号槽、布局、对话框/多窗口、Model/View、数据库、网络、图表、QML/Quick、PyQt、其他。给出建议的章节内分组（`topic_hint`），便于后续写成“历史归档”下的子分组。
- 本机装有 Qt 6.8.1（`C:/Qt/6.8.1/msvc2022_64`），可用 `qmake`/`cmake` 实测挑选的代表性条目能否编译（旧 Qt5 代码常需小改，如 `QRegExp`→`QRegularExpression`），**只做实测记录，不要把改动写回源码**；每个主题至少实测 2–3 个样本，其余标 `build_checked: false`。
- 大量位图（`.bmp`/`.ico`/`.png`）：只在条目确实依赖时才算资源，孤立的二进制资源 `drop-junk`。
- `.pro.user`、`CMakeLists.txt.user`、构建输出一律 `drop-junk`。

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
- [2026-10-21 15:27] cursor：todo → doing
- [2026-10-21 15:44] cursor：doing → review · 单元 208：keep 122 / drop-third-party 49 / drop-junk 37；scoped 2757 文件覆盖 0 遗漏；build_checked 25（通过 18 / 失败 7，Qt 6.8.1 MSVC）。证据：comms/legacy-archive/artifacts/cursor/manifest-qt.json|.md、verify-qt.txt、build-test-qt.txt。待裁决已私信 claude-code（Sample/QmlBook/Charts/PyQt）。
- [2026-10-21 16:00] claude-code：review → done · leader 验收：摘要与零遗漏校验、编译证据已核对；两项 leader 裁决见消息
