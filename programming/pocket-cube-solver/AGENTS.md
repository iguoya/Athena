# 二阶魔方 · 协作规则

仓库级规则在根 `AGENTS.md`。改本应用时以本文为准。

## 定位

- **学习应用**（ADR 0169）：站在初学者怎样把二阶魔方拧回来的角度，分阶段讲，并一章一章把这套解法写成程序：认识、转动、层先法的三个阶段、任意状态、最短解。每章一个能独立编译运行的 gtkmm 窗口，最后一章能解任意状态。
- 目录 `programming/pocket-cube-solver`，id `pocket-cube-solver`，界面名「二阶魔方」，进程 `athena-pocket-cube-solver`，知识点前缀 `cube.`，端口 **1522**，启动器分组「程序设计」，不挂靠。
- **旧版**：`practice/pocket_cube`（id `pocket-cube`，ADR 0060 的项目应用）原地保留作参考，只有状态、转动、3D 视图和展开图，没有求解。本应用不引用它的任何文件；id 不改嫁，所以这里用新 id。
- **出处档位 open**。题目标 `authored`，写明为什么没有现成题。不编造题号；写进 `sources.json` 的条目都是取回核对过的（维基百科两条，核对日期记在 note 里）。题目只考讲解里已经写出的重点、要点、难点、考点。
- **学习方法**（ADR 0113）：主原型**问题解决**（把一个没头绪的状态拆成三个有可判定子目标的阶段），辅**预测–运行**（公式作用在这个状态上会得到什么，先猜再看回放）。每章一个目录、一个窗口，讲解打开就能读，运行按钮始终可用。
- 内容前期要薄（仓库 ADR 0164）：每章核心只写做完就有成果的部分，更深的放「进阶」节，页面上默认折叠。

## 两套技术，各管一件事

- **教程壳**：Tauri 2 + React + TypeScript + Vite。最初复制自 `programming/chinese-chess` 的壳，此后独立演进。壳不画魔方窗口，只读章节、记录作答、按白名单编译并启动某一章。讲解页里另有一份 TypeScript 魔方小模型（`src/cube.ts`）画展开图、立体图和步骤回放。
- **魔方程序**：gtkmm 4，C++20，Meson。七章在 `exercise/`，每章自己的 `meson.build` 和一份 glib 垫片，章与章不抽公共库。每章一个窗口，可执行文件 `cube-01` … `cube-07`，应用 id `cn.athena.pocket_cube_solver.ch01` … `ch07`，都标 `NON_UNIQUE`。每章带一个不依赖 GTK 的测试 `cube-test`。
- Windows 上编译走 MSYS2 mingw64：`PATH` 前置 `C:\msys64\mingw64\bin`，`PKG_CONFIG_PATH=C:\msys64\mingw64\lib\pkgconfig`。源文件加 `-finput-charset=UTF-8`。
- 进度库在用户数据目录 `AthenaPocketCubeSolver/learning.db`，不进 git、由启动器同步到路由器（主仓库 ADR 0155），只存题目的作答，一题一行。环境变量 `ATHENA_POCKET_CUBE_SOLVER_ROOT` 指向应用根（只管内容）。

## 章节

后一章不链接前一章，是前一章长出来的样子，源码另写一份。界面文件 `ui/window.blp` 写控件树，`ui/style.css` 写颜色；C++ 只创建应用、放入自绘视图并接信号。

1. `01-net` 看见魔方：24 张贴纸、8 个角块、展开图怎么读。角块表手抄，测试查它不抄错。
2. `02-turns` 转一转：记号、从 3D 坐标推出转动、层转动动画、撤销、输入记号。转动的数学性质进测试，黄金向量进测试。
3. `03-layer` 做第一层：角块视角、`layer_done`、迭代加深一块一块装。
4. `04-orient` 翻顶面：`top_oriented`、Sune 与反 Sune、宏的最短路搜索。
5. `05-permute` 摆顶层：两个换位公式；三个阶段连成 `solve`。
6. `06-solver` 任意状态：逐格涂色输入、`diagnose` 合法性检查、`normalize` 摆正、`to_input_frame` 换算、均匀随机。
7. `07-optimal` 最短解：角块状态编号、3 674 160 状态的距离表（广度优先，后台线程建表）、查表求解。

每章导语写明它回答的那一个问题，以及故意留到后面的事：不会转的魔方、没有求解的转动、乱着的顶层，都是下一步要收的缺口，不是写漏。每章教程用职责表和一张配合图（步骤图、时序图或依赖图）说明代码组织；魔方讲解图（`section.figure`）是回放图：展开图 + 立体图 + 步骤按钮，也可以是条形图。

## 约定

- **姿势**：白下（D 白）、黄上（U 黄）、绿前（F 绿）、蓝后（B 蓝）、右橙（R 橙）、左红（L 红）。这是真实魔方的手性（红、白、蓝绕角块顺时针，维基百科 Rubik's Cube 的标准配色），测试里断言。只转 U、R、F，DBL 角块永远不动，当参照。
- **两份魔方模型必须一致**：C++（`exercise/*/cube.cc`）和 TypeScript（`src/cube.ts`）各一份，用 `scripts/cube_golden.json` 的黄金向量核对：C++ 在每章 `cube_test.cc` 里断言（01 章没有转动），TypeScript 在 `scripts/check_model.ts` 里断言。改模型要两边一起改、一起重新生成向量。
- **讲解里的回放图要核对**：`scripts/check_content_cubes.ts` 逐张检查记号和 `expect`（写了 `"expect": "solved"` 就是保证走完复原）。改了求解就得重算图里的转法。
- **讲解节三种 role**：`focus`（重点）、`advanced`（进阶，默认折叠）、`experiment`（试一试：`body` 做什么、`predict` 先猜什么、`observe` 实测结果，点开才看）。试一试每条都要在临时副本里真改、真编译、真运行过，`observe` 只写亲眼看到的，不写行号和失败计数（会随源码漂）。
- **题目可带图**：`figure` 是题干配图（只给起点，不许带 `moves`，否则答案摆在题干里），`reveal` 是作答后才出现的回放。预测题的答案必须用 `src/cube.ts` 实算，不口算。图的记号同样由 `scripts/check_content_cubes.ts` 核对。
- **防猜题捷径**：`scripts/check.py` 对全课题目做门禁——答案在任一位置不超过 40%，正确项是最长选项的不超过 50%，选项里不写括号注释（常见错误写进解析，不写进选项）。起因是 2026-10-19 审查时 29 题里 20 题答案在第 2 位、26 题正确项最长。
- **章与章源码有意重复**（ADR 0151 同理由）。改某一处缺陷要看七份里哪几份带着它；`view.cc`、`cube.cc`、`session.cc` 最容易同时涉及多章。
- 讲解数字（平均步数、最长步数、情形数）都是实测或枚举得到的，写在讲解里要和程序对得上；改了求解要重新统计。
- 影响本应用边界的决定写在 `docs/decisions/`。不引用其他应用的路径或代码（包括旧版 `practice/pocket_cube`）。壳只启动白名单里的章节 id，不提供任意命令。
- 学习者改某一章，只改 `workspace/<章>/`（同象棋的做法，本应用 ADR 0001）。`exercise/` 是课程原件。Blueprint 仍是文本，壳里不内置可视化设计器。

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认不编译 gtkmm：检查 app.json、端口、课表、出处契约、每章文件齐备，并用 Node 核对黄金向量和讲解回放图。`--full` 追加教程壳的前端构建和 cargo check。`--native` 才用 meson 编译七章，并跑每章的 `cube-test`（第 7 章的测试要建一次距离表，约 5 秒）。
