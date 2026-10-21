# 历史归档：未收录的条目（postgraduate/algorithms）

来源是旧 GitHub 仓库 `algorithm`、`Linux`（`Algorithm/`）（ADR 0176）。以下内容**没有**进应用的「历史归档」章节；旧仓库只会被设为 archived，历史完整保留，需要时从那里取回。清单与去重证据见 `comms/legacy-archive/artifacts/zcode/`（manifest-algorithms、dedup2-report），逐程序实测事实见 `comms/legacy-archive/artifacts/claude-code/algo-findings.md`。

## 重复与第三方

| 旧路径 | 原因 |
|---|---|
| `Linux/Algorithm/{21-basic,22-recursion,23-divide_and_conconquer,Backtrack,1-速学速用大辞典,DataStructure}` | 与 `algorithm/` 里的同名目录逐文件相同（2023-02 为做 Qt 演示台素材而拷贝），只收 `algorithm/` 里的规范版 |
| `Linux/Algorithm/qdarkstyle`（481 个文件） | QDarkStyleSheet 官方库的整套拷贝，是演示台的暗色皮肤依赖，非自写 |
| `Linux/Algorithm/Algorithm`（ELF 可执行文件） | LoongArch 架构的编译产物提交进了仓库 |
| `Linux/Algorithm/images/*.svg、background.jpg` | 演示台的图标与背景资源，与算法无关 |

## 没有内容价值

| 旧路径 | 原因 |
|---|---|
| `algorithm/backtracking/substring` | 只有 Hello World |
| `algorithm/DataStructure/recursion` | C++ 版递归的计划没有落地（`main.cpp` 只打印 Hello World）；真正的递归练习在 `22-recursion` |
| `algorithm/1-速学速用大辞典/backpack` | 号称背包问题，实际只打印一个 5×5 数组各元素的地址，且依赖不存在的 `../stack/stack.h` |
| `algorithm/docs`（算法笔记 7 章与数据结构笔记，约 13 KB）、`algorithm/markdown`、`algorithm/vuepress`、`5-LineChart.md` | 提纲式笔记，大半是标题与 mermaid 流程图；markdown、vuepress 与 chart.js 是前端文档工具练习，与算法无关 |
| `algorithm/21-basic` | C 语言基础，归 `programming/linux` 的历史归档（尚在整理） |

## 归入其他应用

| 旧路径 | 去向 |
|---|---|
| `Linux/Algorithm` 的 Qt 演示台（`main.cpp`、`mainwindow.*`、`Abstract/`、`Deduction/`、`DivideConquer/`、`Recursion/`、`Exhaustion/`） | `programming/qt`，条目 `qt.arc.algorithm_console` |
