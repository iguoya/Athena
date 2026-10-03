# ADR 0002：章节与知识点跟开源教材走，不自拟知识体系

- 日期：2026-09-14
- 状态：已接受
- 修正：ADR 0001 第 1 条里按 C++ 课类比出来的章名（对象与字节、函数与地址、堆与寿命）

## 背景

首页改成章级图谱之后，章名是对着主程序 C++（类型与表达式 → 引用 → RAII）
类比出来的：「对象与字节」「函数与地址」在开源 C 教程里都不是独立一章。
Beej 把「把指针传进函数」放在指针章；K&R 把指针和数组写在同一章。
自拟目录看起来完整，和口碑教材对不上，后面写教案也没有节号可核。

## 决策

1. **主目录跟 [Beej's Guide to C](https://beej.us/guide/bgc/) 教程卷的核心顺序。**
   跳过 Hello World、流程控制和作为语法的函数章（Athena 不把 C 写成入门语法课）。
   进入本应用的是 Beej 从「内存与变量 / 指针」起的那条脊：

   `内存与变量 → 指针 → 数组 → 字符串 → 结构体 → 动态分配`

   对应 Beej §5.1 → §5 → §6 → §7 → §8 → §12。
2. **程序地址空间跟 [Dive Into Systems](https://diveintosystems.org/) 第 2 章。**
   该章开篇写明先讲 parts of program memory，再讲指针和动态分配。Beej §5.1
   只讲「字节有地址」，不画栈 / 堆 / 数据段，这块用 DIS 补，不另造章名。
3. **深度用 [Modern C](https://gustedt.gitlabpages.inria.fr/modern-c/) Level 2 核对。**
   Pointers、The C memory model、Storage 三章用来检查有没有讲浅了或用词漂了。
   不采用它 Level 0–1 的「先控制流和派生类型、指针放到 Level 2」作为本应用目录——
   那是给已有编程经验、按 ISO 分层的教材，和 Beej / DIS 给学习者的顺序不同。
4. **每个章节和知识点在 `curriculum.json` 里带 `source_refs`。**
   `id` 指向 `content/sources/catalog.json`，`loc` 写到节号。对不上节号的节点不要加。
5. **不整段复制教材正文。** 参考的是该讲哪一条、先修是什么；教案用自己的内存条和对照写。
6. **本地副本与出题规则见 ADR 0003。** 写课前打开 `content/sources/reference/` 里对应文件。
7. **语义对错以 C23 为准，见 ADR 0004。** 教材管章序和讲法，标准管这条在现行语言里是否仍真。

## 后果

- 「函数与地址」不再是一章：Beej §5.4 Passing Pointers as Arguments 归指针章。
- 数组紧跟指针：K&R 第 5 章和 Beej §6.6 / §11.2 都把「数组名和指针」当作同一件事。
- 已有两节教案（字节编址、指针存地址）对上 Beej §5.1 / §5.2，文件路径不变。
