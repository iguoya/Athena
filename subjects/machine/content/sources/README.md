# 课表依据

章节和知识点必须能在 `sources/catalog.json` 登记的教材里对上节号，
见 [ADR 0002](../../docs/decisions/0002-curriculum-from-open-textbooks.md)、
[ADR 0003](../../docs/decisions/0003-local-sources-and-sourced-exercises.md)。
语义对错以 C23 为准，见 [ADR 0004](../../docs/decisions/0004-c23-language-baseline.md)。

写新节前先打开 `reference/` 里对应文件，核对该讲什么、先修是什么；不要按 C++ 课
的章名类比出一套 C 目录，也不要凭印象出题。

刷新本地副本：`subjects/machine/scripts/fetch-sources.py`。

| id | 教材 | 本地 | 在本课表里干什么 |
|---|---|---|---|
| `beej-bgc` | [Beej's Guide to C](https://beej.us/guide/bgc/)（[GitHub](https://github.com/beejjorgensen/bgc)） | `reference/github/beej-bgc/` | 主目录：指针 → 数组 → 字符串 → 结构体 → malloc |
| `dis` | [Dive Into Systems](https://diveintosystems.org/) | `reference/dive-into-systems/` | 程序地址空间（代码 / 数据 / 栈 / 堆）；汇编线取第 6、7、9、10 章 |
| `modern-c` | [Modern C](https://gustedt.gitlabpages.inria.fr/modern-c/) | `reference/modern-c/`（PDF 需手动另存） | 核对「内存模型 / Storage」的深度 |
| `c-faq` | [C FAQ](https://c-faq.com/) | `reference/c-faq/`（HTML 不进 git） | 指针、数组、malloc 误区 |
| `c23` | [ISO/IEC 9899:2024](https://www.iso.org/standard/82075.html) | `reference/c23/`（N3220 PDF 不进 git） | 语义对错的基准（ADR 0004） |
| `sysv-abi` | [x86-64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI) | `reference/sysv-abi/`（PDF 不进 git） | System V 调用约定（汇编线基准 ABI） |
| `ms-x64-abi` | [Microsoft x64 调用约定](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention) | `reference/ms-x64-abi/` | Windows x64 调用约定（对照） |
| `aapcs64` | [Arm AAPCS64](https://github.com/ARM-software/abi-aa) | `reference/aapcs64/` | ARM64 调用约定 |
| `intel-sdm` | [Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html) | `reference/intel-sdm/`（PDF 不进 git） | x86-64 指令参考 |
| `gnu-as` | [GNU as 手册](https://sourceware.org/binutils/docs/as/) | `reference/gnu-as/` | AT&T 与 Intel 语法、汇编器写法（ADR 0007） |
| `arm-isa` | [Arm A64 ISA](https://developer.arm.com/documentation/ddi0602/latest/) | 不落本地 | ARM64 指令参考，只引用网址 |

K&R 第 5 章把指针和数组写在一起，用来解释为什么数组紧跟指针；全书正文不在
GitHub 上公开，不作为逐条措辞来源。
