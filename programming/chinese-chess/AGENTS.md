# 中国象棋 · 协作规则

仓库级规则在根 `AGENTS.md`。改本应用时以本文为准。

## 定位

- **学习应用**（ADR 0151）：用做一盘中国象棋来学桌面程序怎么一步步长出来。要教会人 gtkmm 窗口、布局、自绘和一份走子规则。每一章的主路径是界面文件，代码搭界面用来对照。
- 目录 `programming/chinese-chess`，id `chinese-chess`，进程 `athena-chinese-chess`，知识点前缀 `chess.`，端口 **1513**，启动器分组「程序设计」，不挂靠。
- **出处档位 open**。题目标 `authored`，写明为什么没有现成题。不编造题号。题目只考讲解里已经写出的重点、要点、难点、考点。
- **学习方法**（ADR 0113）：主原型**真做校验**，辅**预测–运行**。每章一个目录、两个能独立编译运行的窗口（本应用 ADR 0002）。讲解打开就能读，两个运行按钮始终可用，界面文件版在前。
- 第一版只做到人和人对下、棋子按规则移动。没有引擎。长将、长捉不判。困毙算走方负。

## 两套技术，各管一件事

- **教程壳**：Tauri 2 + React + TypeScript + Vite。壳最初照 `programming/python` 的薄壳改，此后独立演进。壳不画棋盘，只读章节、记录作答、按白名单编译并启动某一章。
- **棋盘**：gtkmm 4，C++20，Meson。五章在 `exercise/`，每章自己的 `meson.build` 和一份 glib 垫片，章与章不抽公共库。同一章的两个窗口可以编译这一章的 `BoardView`、`Position` 和 `Session`。界面文件版 id 是 `cn.athena.chinese_chess.ch01ui` … `ch05ui`，代码版是 `ch01` … `ch05`，都标 `NON_UNIQUE`。
- Windows 上编译棋盘走 MSYS2 mingw64：`PATH` 前置 `C:\msys64\mingw64\bin`，`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`。源文件加 `-finput-charset=UTF-8`。
- 进度库 `progress/learning.db` 随仓库走，只存题目的作答，一题一行。发行包退回用户数据目录 `AthenaChineseChess`。环境变量 `ATHENA_CHINESE_CHESS_ROOT` 指向应用根。

## 章节

1. `01-window` 空窗口。
2. `02-layout` 棋盘在左、侧栏在右，按钮先不做事。
3. `03-board` 按交叉点画棋盘。
4. `04-pieces` 开局棋子，不能走。
5. `05-move` 合法走子、记谱、悔棋、新局、将军、将死、困毙。规则和测试只在这一章。

后一章不链接前一章。同一章里，界面文件版是教程的主路径：`ui/window.blp` 写控件树，`ui/style.css` 写颜色，C++ 只创建应用、放入自绘棋盘并接信号。`code/main.cc` 用代码搭出同一扇窗，篇幅用来对照。棋盘绘制和走子规则不进界面文件。

每章导语写明它回答的那一个问题，以及故意留到后面的事：空窗、按不了的按钮、只有线的棋盘、画死的子，都是下一步要收的缺口，不是写漏。每章教程用职责表（每个函数做什么、和谁协作）和依赖图（实线是调用，箭头指向被调用的一方；虚线是信号）说明代码组织。打开窗口、重画、算合法着这种过程用步骤图。一次点击的先后用时序图。源码注释写函数意图和配合，不写语法。五章的划分保持不变。

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认不编译 gtkmm。`--full` 只构建教程壳。`--native` 才 meson 编译五章十个窗口，并跑第 5 章的规则测试。

## 约定

- 影响本应用边界的决定写在 `docs/decisions/`。
- 不引用其他应用的路径或代码。
- 壳只启动白名单里的章节 id，不提供任意命令。
- 学习者改某一章，只改 `workspace/<章>/`（本应用 ADR 0003）。`exercise/` 是课程原件。界面「在 VS 2022 中打开」在没有副本时复制那一章（跳过 `build/`），第 3 章起同时复制 `workspace/assets`。运行按钮有工作副本就编译副本。还原删掉这一章的副本。Blueprint 仍是文本，壳里不内置可视化设计器。
