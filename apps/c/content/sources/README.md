# 课表依据

章节和知识点必须能在 `sources/catalog.json` 登记的教材里对上节号，
见 [ADR 0002](../../docs/decisions/0002-curriculum-from-open-textbooks.md)、
[ADR 0003](../../docs/decisions/0003-local-sources-and-sourced-exercises.md)。
语义对错以 C23 为准，见 [ADR 0004](../../docs/decisions/0004-c23-language-baseline.md)。

写新节前先打开 `reference/` 里对应文件，核对该讲什么、先修是什么；不要按 C++ 课
的章名类比出一套 C 目录，也不要凭印象出题。

刷新本地副本：`apps/c/scripts/fetch-sources.py`。

| id | 教材 | 本地 | 在本课表里干什么 |
|---|---|---|---|
| `beej-bgc` | [Beej's Guide to C](https://beej.us/guide/bgc/)（[GitHub](https://github.com/beejjorgensen/bgc)） | `reference/github/beej-bgc/` | 主目录：指针 → 数组 → 字符串 → 结构体 → malloc |
| `dis` | [Dive Into Systems](https://diveintosystems.org/) | `reference/dive-into-systems/` | 程序地址空间（代码 / 数据 / 栈 / 堆） |
| `modern-c` | [Modern C](https://gustedt.gitlabpages.inria.fr/modern-c/) | `reference/modern-c/`（PDF 需手动另存） | 核对「内存模型 / Storage」的深度 |
| `c-faq` | [C FAQ](https://c-faq.com/) | `reference/c-faq/`（HTML 不进 git） | 指针、数组、malloc 误区 |
| `c23` | [ISO/IEC 9899:2024](https://www.iso.org/standard/82075.html) | `reference/c23/`（N3220 PDF 不进 git） | 语义对错的基准（ADR 0004） |

K&R 第 5 章把指针和数组写在一起，用来解释为什么数组紧跟指针；全书正文不在
GitHub 上公开，不作为逐条措辞来源。
