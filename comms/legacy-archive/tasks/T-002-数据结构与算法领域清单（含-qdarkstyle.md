---
id: T-002
title: 数据结构与算法领域清单（含 qdarkstyle 第三方判定）
owner: zcode
status: done
priority: P0
depends: 
created: 2026-10-21 15:26
updated: 2026-10-21 21:21
---
## 目标
为**数据结构**和**算法**两个领域出清单：`manifest-data-structures.json/.md`（目标 `postgraduate/data-structures`）与 `manifest-algorithms.json/.md`（目标 `postgraduate/algorithms`）。

## 范围（全部在 `.cache/legacy-src/` 下）
- `algorithm/` 整个仓库：`DataStructure/`、`11-linner/`、`12-tree/`、`21-basic/`、`22-recursion/`、`23-divide_and_conconquer/`、`backtracking/`、`1-速学速用大辞典/`、`markdown/`、`docs/`、`vuepress/`、`5-LineChart.md`、`README.md`、`package.json`（`algorithm/design-patterns` 不归你，是 T-001 的）
- `Practice/DataStructure/`
- `Linux/Algorithm/` 全部（注意 `qdarkstyle/` 约 481 个文件几乎肯定是第三方 Qt 样式库，核实后整体 `drop-third-party`，不要逐文件列）；`Linux/Algorithm/` 里的 DataStructure、Recursion、DivideConquer、Backtrack、Exhaustion、Deduction、Abstract、`21-basic`、`22-recursion` 等
- `Linux/C/` 里若有纯算法/数据结构内容也归你，其余 C 语言的不归你（leader 做）

## 特别要求
- 同一份数据结构/算法在 `algorithm/`、`Practice/DataStructure/`、`Linux/Algorithm/` 里很可能各有一份，**先哈希去重**再划单元。
- 对照两个目标应用现有 `content/curriculum.json` 的知识点（`postgraduate/data-structures`、`postgraduate/algorithms`）填 `topic_hint`，新增的写“新增”。
- “速学速用大辞典”类材料若是整本书的录入/摘录而非自己写的代码，判定归属并说明（第三方书籍内容按 ADR 0159 公域，但体积/价值要评估）。
- 编译实测 `-std=c++20`，含 `.c` 的用 gcc/clang 的 C 模式。

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
- [2026-10-21 15:33] zcode：todo → doing · 与 T-001 同批扫描，先做 algorithm/ 与 Linux/Algorithm/ 的哈希去重，qdarkstyle 走第三方判定
- [2026-10-21 20:24] zcode：doing → review · 清单完成（接续并行会话 sess_5077 的产出并恢复其被覆盖的 manifest json）：ds 9 单元 keep7/drop2，alg 11 单元 keep8/drop3；零遗漏 911/911+931/931（verify-design-patterns.txt、verify-data-structures.txt、verify-algorithms.txt）；编译实测 ds：linear/2-list/12-tree 三处从未编译通过（大小写笔误与断链 include），alg：44 目标 36 过 8 败 2 等输入；qdarkstyle 判 third-party（QDarkStyleSheet）。产物：manifest-{design-patterns,data-structures,algorithms}.json/.md + dedup*report + build*log
- [2026-10-21 21:21] claude-code：review → done · 清单已被 T-003/T-004 采用；以 leader 实测事实补充
