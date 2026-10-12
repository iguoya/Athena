# 中国象棋

用 gtkmm 把一盘桌面象棋按章节做出来。教程是 Tauri 窗口，棋盘是每一章自己的 C++ 程序。

红方在下，棋盘在左，右边是黑方、棋谱、红方和「新局 / 悔棋」。当前这一版人和人对下，棋子按规则走。没有电脑对手。长将、长捉不判；无子可走算困毙，走方负。

## 五章

每章一个目录，自己的 `meson.build`，章与章不共用库。每一章有两个窗口：界面文件版是要学的写法，代码版用来对照。后一章是前一章长出来的样子，源码是另写的一份。

| 目录 | 打开之后能看见什么 |
| --- | --- |
| `exercise/01-window` | 一扇标题为「中国象棋」的空窗口 |
| `exercise/02-layout` | 木色棋盘占位、右侧栏、还不能按的按钮 |
| `exercise/03-board` | 交叉点棋盘、九宫、河界、坐标，没有棋子 |
| `exercise/04-pieces` | 开局棋子画在交叉点上，不能走 |
| `exercise/05-move` | 点选、合法走子、吃子、记谱、悔棋、新局、将军和困毙 |

教程先讲界面文件，再放一节较短的代码对照。两个运行按钮随时可用，界面文件版在前面。题目从讲解里抽，答之前讲解已经在页面上。

## 打开

```sh
launcher open chinese-chess
```

只看教程页、不编棋盘：`pnpm run dev`，浏览器开 http://localhost:1513 。

单独编某一章（Windows 上要先把 MSYS2 mingw64 放进 `PATH`，并设置 `PKG_CONFIG_PATH`）：

```sh
cd exercise/05-move
meson setup build
meson compile -C build
meson test -C build
# 编出来的是 build/chess-05-ui.exe 和 build/chess-05-code.exe
```

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认检查不编译 gtkmm，CI 因此跑得过。`--native` 在本机把五章都编一遍，并跑第 5 章的走子测试。
