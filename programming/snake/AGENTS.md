# 贪吃蛇 · 协作规则

仓库级规则在根 `AGENTS.md`。改本应用时以本文为准。

## 定位

- **学习应用**（ADR 0153）：用做一只贪吃蛇来学游戏程序怎么一步步长出来。要教会人
  游戏循环、固定步进、输入缓冲、状态机、插值渲染和一段可测试的规则。每一章的主路径
  就是那份单文件主程序——raylib 是 immediate mode，没有界面文件层，讲解直接对着
  `src/main.cc` 讲。
- 目录 `programming/snake`，id `snake`，进程 `athena-snake`，知识点前缀 `snake.`，
  端口 **1514**，启动器分组「程序设计」，不挂靠。
- **出处档位 open**。题目标 `authored`，写明为什么没有现成题。不编造题号。题目只考
  讲解里已经写出的重点、要点、难点、考点。
- **学习方法**（ADR 0113）：主原型**真做校验**，辅**预测–运行**。每章一个目录、一个
  能独立编译运行的窗口。讲解打开就能读，运行按钮始终可用。
- 只有键盘输入，没有 AI 对手。最高分演示性持久化在进程工作目录，真实落点（用户数据
  目录）在第 4 章讲解里说明。

## 两套技术，各管一件事

- **教程壳**：Tauri 2 + React + TypeScript + Vite。壳最初照 `programming/chinese-chess`
  的壳改，此后独立演进。壳不画蛇，只读章节、记录作答、按白名单编译并启动某一章。
- **贪吃蛇**：raylib 5，C++20，CMake。五章在 `exercise/`，每章自己的 `CMakeLists.txt`
  和单文件主程序，章与章不抽公共库（第 5 章章内的 `logic.hh` 是本章的教学点，不是跨章
  共享）。第 5 章带一份不依赖 raylib 的逻辑测试。
- raylib 的来源三选一：MSYS2 `pacman -S mingw-w64-x86_64-raylib mingw-w64-x86_64-cmake
  mingw-w64-x86_64-ninja`（Windows 本机路径）、vcpkg、发行版包。CMake 先找 CMake 包
  配置，找不到退到 pkg-config。
- Windows 上编译走 MSYS2 mingw64：`PATH` 前置 `C:\msys64\mingw64\bin`。HUD 文字用
  英文——raylib 默认字体只带 ASCII，中文化要 LoadFontEx 加载 TTF，不在这门课里。
- 进度库 `progress/learning.db` 随仓库走，只存题目的作答，一题一行。发行包退回用户
  数据目录 `AthenaSnake`。环境变量 `ATHENA_SNAKE_ROOT` 指向应用根。

## 章节

1. `01-window` 空窗口与游戏循环，「每帧都在重画」看得见。
2. `02-grid` 格子世界与固定节拍，累加器补步。
3. `03-snake` 蛇身与输入两条队列，吃食物、撞墙、咬自己。
4. `04-state` 四相状态机、计分、最高分。
5. `05-polish` 逻辑抽进 `logic.hh` 加测试，插值渲染，合成音效。规则只在这一章。

后一章不链接前一章。每章都是上一章长出来的样子，源码是另写的一份，有意重复。
每章的程序目标名是 `snake-01` … `snake-05`。

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认不编译 raylib。`--full` 只构建教程壳。`--native` 才 cmake 编译五章，并跑第 5 章
的逻辑测试。

## 约定

- 影响本应用边界的决定写在 `docs/decisions/`。
- 不引用其他应用的路径或代码。
- 壳只启动白名单里的章节 id，不提供任意命令。
