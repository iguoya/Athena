# 贪吃蛇

用 raylib 把一只贪吃蛇按章节做出来。教程是 Tauri 窗口，蛇是每一章自己的 C++ 程序。

五个程序长得越来越像一只真正的游戏：从「每帧都在重画」的一扇窗，到格子与固定节拍，
到两条队列撑起的玩法，到四相状态机，最后是插值、声音和一段能脱离窗口测试的规则。

## 五章

每章一个目录，自己的 `CMakeLists.txt`，章与章不共用库。后一章是前一章长出来的样子，
源码是另写的一份。第 5 章是当前能玩的版本。

| 目录 | 打开之后能看见什么 |
| --- | --- |
| `exercise/01-window` | 一扇窗，方块随时间滑动，帧计数在跳 |
| `exercise/02-grid` | 网格上一格按 5 Hz 的节拍走，渲染 60 fps |
| `exercise/03-snake` | 完整玩法：吃食物变长，撞墙、咬自己即停，R 重开 |
| `exercise/04-state` | 开始 / 暂停 / 结束三相齐备，计分与最高分 |
| `exercise/05-polish` | 蛇身插值滑动、合成音效、逻辑测试；WASD 或方向键 |

题目从讲解里抽，答之前讲解已经在页面上。第 5 章的规则在 `logic.hh`，测试在
`tests/logic_test.cc`，不依赖 raylib。

## 打开

```sh
launcher open snake
```

只看教程页、不编蛇：`pnpm run dev`，浏览器开 http://localhost:1514 。

单独编某一章（Windows 上要先把 MSYS2 mingw64 放进 `PATH`，并装 raylib：
`pacman -S mingw-w64-x86_64-raylib mingw-w64-x86_64-cmake mingw-w64-x86_64-ninja`）：

```sh
cd exercise/05-polish
cmake -B build
cmake --build build
ctest --test-dir build
# 编出来的是 build/snake-05.exe
```

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认检查不编译 raylib，CI 因此跑得过。`--native` 在本机把五章都编一遍，并跑第 5 章
的逻辑测试。
