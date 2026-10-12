# 贪吃蛇 · 协作规则

仓库级规则在根 `AGENTS.md`。改本应用时以本文为准。

## 定位

- **学习应用**（ADR 0153、应用级 ADR 0002）：用做一只贪吃蛇来学游戏程序怎么一步步长
  出来。教学法的本质是**演化的显式化**：每一章回答上一章留下的一个真实问题，前一阶段
  的凑合（第三章的裸 if 重开）保留到被收编的那一章；章数由演化阶段数决定，不设上限
  也不凑数。每一章的主路径就是那份单文件主程序——raylib 是 immediate mode，没有界面
  文件层，讲解直接对着 `src/main.cc` 讲。
- 目录 `programming/snake`，id `snake`，进程 `athena-snake`，知识点前缀 `snake.`，
  端口 **1514**，启动器分组「程序设计」，不挂靠。
- **出处档位 open**。题目标 `authored`，写明为什么没有现成题。不编造题号。题目只考
  讲解里已经写出的重点、要点、难点、考点。
- **学习方法**（ADR 0113）：主原型**真做校验**，辅**预测–运行**。每章一个目录、一个
  能独立编译运行的窗口。讲解打开就能读，运行按钮始终可用。
- 只有键盘输入，没有 AI 对手。最高分演示性持久化在进程工作目录，真实落点（用户数据
  目录）在第 7 章讲解里说明。

## 两套技术，各管一件事

- **教程壳**：Tauri 2 + React + TypeScript + Vite。壳最初照 `programming/chinese-chess`
  的壳改，此后独立演进。壳不画蛇，只读章节、记录作答、按白名单编译并启动某一章。
- **贪吃蛇**：raylib 5，C++20，CMake。八章在 `exercise/`，每章自己的 `CMakeLists.txt`
  和单文件主程序，章与章不抽公共库（章内的 `logic.hh` 是第七、八章的教学点，不是跨章
  共享）。第 7、8 章各带一份不依赖 raylib 的规则测试。
- **raylib 不要求预装**：系统有（MSYS2 / vcpkg / 发行版包）就用系统的，没有时 CMake
  FetchContent 自动拉 5.5 源码现场编译——它是单文件 C 库，几秒编完。八章共享
  `.cache/fetchcontent` 一份下载与编译缓存（已 gitignore）。
- Windows 上编译：系统 CMake + Visual Studio C++ 工作负载即可，MSYS2 的 cmake 也可以；
  mac、Linux 用各自的标准工具链。两条已踩过的坑都修在 CMakeLists 里：MSVC 要
  `/utf-8`（默认按系统代码页读源文件，UTF-8 中文注释会吞掉换行）；多配置生成器的
  exe 输出用 `RUNTIME_OUTPUT_DIRECTORY` 固定回 `build/` 根，ctest 用
  `$<TARGET_FILE:...>` 并带 `-C Debug`。
- HUD 文字用英文——raylib 默认字体只带 ASCII，中文化要 LoadFontEx 加载 TTF，不在这门
  课里。
- 进度库 `progress/learning.db` 随仓库走，只存题目的作答，一题一行。发行包退回用户
  数据目录 `AthenaSnake`。环境变量 `ATHENA_SNAKE_ROOT` 指向应用根。

## 章节

1. `01-window` 空窗口与游戏循环，「每帧都在重画」看得见。
2. `02-grid` 格子世界与固定节拍，累加器补步。
3. `03-body` 固定长度的蛇，方向直接改写；**折叠 bug 有意留在这章**；裸 if 重开是有意的凑合。
4. `04-input` 输入缓冲：为第三章的 bug 发明的机制，反向丢弃、容量三格。
5. `05-food` 食物与变长；变长让「咬到自己」才成为死法。
6. `06-state` 四相状态机，收编第三章的凑合；暂停不补时间。
7. `07-score` 计分挂在新吃事件上，最高分与持久化落点。
8. `08-logic` 规则搬进 `logic.hh`（零 raylib 依赖）；只搬运，不改行为，不带测试。
9. `09-test` 程序与第八章逐行相同，差别全在 tests/：断言、CTest、构建图上看得见的分离。
10. `10-polish` 插值渲染、合成音效；`logic.hh` 演化出吃到加速，测试跟着长。

台阶形态（ADR 0003）：bug 先被看见（3）再被发明出来的机制修掉（4）；凑合先被留下
（3）再被收编（6）；规则先出窗（8）再有第一个客户——测试（9）；改行为（10 的加速）
与加呈现（10 的插值、声音）都是小增量。

另有第 11 节 `snake.design`「成品长成了什么样」：不是演化台阶，是以设计总览为蓝本的导读
（ADR 0005），`exercise` 与第 10 章共用 `10-polish`，讲解文件是 `content/chapters/11-design.json`，
文件栏第一项是 `docs/design/overview.md`。课表共 11 节，壳按文件名排序。

后一章不链接前一章。每章都是上一章长出来的样子，源码是另写的一份，有意重复。
目标名 `snake-01` … `snake-10`；第 9、10 章各带 `logic-test` 目标。

## 验证

```sh
python3 scripts/check.py
python3 scripts/check.py --full
python3 scripts/check.py --native
```

默认不编译 raylib。`--full` 只构建教程壳。`--native` 才 cmake 编译十章，并跑第 9、10 章
的规则测试。

## 约定

- 影响本应用边界的决定写在 `docs/decisions/`。
- **成品设计总览**在 `docs/design/overview.md`（应用级 ADR 0005），描述第 10 章成品，是
  Markdown 正本。改 `logic.hh` 的接口、规则或不变式时同步改它和追溯矩阵；`check.py` 会
  核对矩阵、`@covers` 标记、接口表与 `logic.hh`。测试按需求编号铺在
  `exercise/10-polish/tests/rules_test.cc`。
- 不引用其他应用的路径或代码。
- 壳只启动白名单里的章节 id，不提供任意命令。
