# 二阶魔方

从初学者怎样把二阶魔方拧回来出发，一章一章写出一个能解任意状态的程序。教程是 Tauri 窗口，魔方是每一章自己的 gtkmm 程序。

白色在下、绿色在前。魔方先能看、能转，再按层先法的三个阶段做第一层、翻顶面、摆顶层，然后接住任意状态（涂色输入、合法性检查、自动摆正），最后用一张 367 万状态的距离表给出最短解。每个阶段、每一步转动都在窗口里看得见：立体图、展开图、阶段标签、转法条一起走。

## 七章

每章一个目录、自己的 `meson.build`，章与章不共用库。后一章是前一章长出来的样子，源码是另写的一份。

| 目录 | 打开之后能看见什么 |
| --- | --- |
| `exercise/01-net` | 展开图；点一格，圈出它所在角块的三张贴纸 |
| `exercise/02-turns` | 立体图和展开图；九个转法按钮、记号输入、动画、撤销、打乱 |
| `exercise/03-layer` | 打乱后「做第一层」：一块一块装，逐步回放 |
| `exercise/04-orient` | 再加「翻顶面」：Sune 与反 Sune |
| `exercise/05-permute` | 再加「摆顶层」：三个阶段一条龙复原 |
| `exercise/06-solver` | 逐格涂色输入真魔方；合法性检查；自动摆正；三阶段回放 |
| `exercise/07-optimal` | 再加「最短解」：距离表，平均不到 9 步，最多 11 步 |

## 打开

```sh
launcher open pocket-cube-solver
```

只看教程页、不编魔方窗口：`pnpm run dev`，浏览器开 http://localhost:1522 。

单独编某一章（Windows 上要先把 MSYS2 mingw64 放进 `PATH`，并设置 `PKG_CONFIG_PATH`）：

```sh
cd exercise/06-solver
meson setup build
meson compile -C build
meson test -C build
# 编出来的是 build/cube-06.exe
```

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认检查不编译 gtkmm，CI 因此跑得过。`--native` 在本机把七章都编一遍，并跑每章的测试。

## 旧版

[`practice/pocket_cube`](../../practice/pocket_cube) 是更早的 2 阶魔方项目应用（状态、转动、3D 视图、展开图，没有求解），原地保留作参考。
