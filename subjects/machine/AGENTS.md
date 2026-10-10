# Athena Machine（C 与机器）— 项目协作规则

本文档是 **`subjects/machine` 独立应用** 的项目级指令，不依赖任何其他应用。改本应用时以本文为准。

> **改造进行中（ADR 0005、0006）**：本应用原名 `c`；重组前的状态在 tag `pre-machine-reorg`。
> 课程图已重写为三条线（本文「定位」「教学结构」），来源已进 catalog；汇编线只有「读懂汇编」写了两节
> （寄存器、操作数），其余汇编章和全部联合章仍是**灰章**。多目标实验已有命令行版（`labs/` + `scripts/lab.py`），三个目标在 Windows 上
> 都实测跑通（`sysv-x64`、`aarch64-linux` 经 WSL）；**应用里的实验台界面还没接**，仍是旧的
> `playground/`。这些按 ADR 0005 的步骤陆续补，没补之前不要把它们写成已有。

## 定位

- 目标：把 C 与汇编结合起来学习，**同时理解两者**，看清高层与底层如何统一（ADR 0005）。
  每一章既有理论讲解，也有可运行的实践练习。
- 章分三条线：**C 独立**（只讲 C 本身）、**汇编独立**（x86-64 为主线，ARM64 作对照）、
  **联合**（C 与汇编怎么对应）。线的名字与颜色在 `curriculum.json` 的 `tracks`，不写死在界面里。
- **C 的语义以 C23 为准**（ADR 0004）。汇编输出一律是「某个实现的一次结果」，**不能当作 C 规则的
  证据**；关于寄存器、调用约定的结论只来自 ABI 与 ISA 手册。
- **教案用 QML 写**（ADR 0042），不是启动一个演示用的 C 程序。
- 原 LVGL 小程序保留在 `playground/`，需要时单独构建，**不是**图谱入口。
- **学习方法原型（ADR 0113）**：主原型**预测–运行**，辅**机制模拟**。先预测程序输出再运行，并对照内存与寄存器视图——这门课的核心是让看不见的内存布局与指令执行可见，所以「看机器状态」是对照环节的主角。

## 教学结构

知识图谱节点是**章**，不是知识点。点进一章之后，大纲里才有该章的知识点路线图；教案从那张图
点进来。

| 层 | 本应用 |
|---|---|
| 知识图谱 | 首页 17 章（C 8 · 联合 5 · 汇编 4）+ `prerequisites`，卡片上标线 |
| 教学大纲 | 点章之后：方向 + 知识点路线图（灰章只有题注与简介） |
| 教学过程 | 章内路线图点白卡片才进入 |
| 教学实验 | 多目标实验 `labs/<id>/`，命令行 `scripts/lab.py`（ADR 0006）；应用内界面待做，现仍是旧 `playground/` |
| 随堂考核 | `Checkpoint.qml` + `exercises.json`：多题、有解析 |

**先修方向有规矩（ADR 0005 第 3 条，`scripts/check.py` 校验）**：C 独立章只依赖 C 独立章；
汇编独立章只可依赖 C 的「内存与变量」，不得依赖联合章；联合章必须**同时直接**依赖至少一个 C 独立章和
一个汇编独立章。知识点 id 按线分段：`machine.c.*` / `machine.asm.*` / `machine.joint.*`，前缀必须
和所在章的 `track` 一致。

C 独立章只讲 C 的语义，引用、RAII、模板这类别的语言特有的内容不在本应用里讲。C 侧发挥的是内存条、
地址箭头和真实的 C 程序，这些只让教材里的命题被看见，不得发明一条教材没有的规则（例如把本机小端写成
C 的保证）。

## 技术栈

- **壳**：Qt 6 Quick / Qml（C++20）
- **教案**：`qml/lessons/*.qml` + 共用组件 `qml/components/`
- **课表**：`content/curriculum.json`（章、先修、难度、指向哪份 QML、`source_refs`）
- **题库**：`content/exercises.json`（随堂 / 课后，每题带 `source_refs`）
- **进度**：后续自建库，前缀 `machine.`（ADR 0037、0005），位置按 ADR 0053 放
  `progress/learning.db` 并随仓库走；本期考核只当场计分


## 目录

| 路径 | 职责 |
|---|---|
| `qml/pages/GraphPage.qml` | 首页**章**知识图谱 |
| `qml/pages/OutlinePage.qml` | 一章的教学大纲 + 该章知识点路线图 |
| `qml/lessons/` | 各节教学过程 |
| `qml/components/` | 章卡片、知识点节点、大纲区块、对照、内存条、随堂考核 |
| `content/curriculum.json` | 章与知识点导航 |
| `content/exercises.json` | 随堂与课后题 |
| `content/sources/` | 教材目录与本地副本 |
| `src/` | C++ 壳：读课表、从磁盘加载 QML、监视文件热加载 |
| `scripts/fetch-sources.py` | 把公开教材拉到 `content/sources/reference/` |
| `labs/<id>/` | 多目标实验：`fn.c` 参考实现、`main.c` 固定驱动、`asm/` 下每个目标一份可运行的骨架、`lab.json` |
| `content/asm/<id>/` | 观察层：clang 为各目标、各语法、`-O0`/`-O2` 预生成的汇编，由 `lab.py gen` 生成，别手改 |
| `scripts/lab.py` | `doctor` 体检、`gen` 预生成、`run` 真跑、`check` 校验（`check.py` 会调用） |
| `playground/` | 保留的 LVGL 小程序，不从图谱启动 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `launcher` 执行（ADR 0046） |

## 开发

```sh
cd subjects/machine
launcher open machine
```

改 QML / `curriculum.json` / `exercises.json` 保存后窗口会自己重新加载。只有改
`src/` 才需要让脚本再编一次 C++。本机需要 Qt 6（Homebrew `qt@6`）。

多目标实验（需要 clang；Windows 上 `sysv-x64`、`aarch64-linux` 经 WSL 的 Ubuntu 运行，ADR 0006 第 2 条的
工具清单还要加上 `libc6-dev`，否则 gcc 找不到 `stdio.h`，`doctor` 会指出缺什么）：

```sh
python3 scripts/lab.py doctor       # 缺什么、怎么装、各目标能否真跑
python3 scripts/lab.py gen sum      # 改了 fn.c 之后重新生成观察层，否则 check 会报过期
python3 scripts/lab.py run sum      # 在本机原生目标上编译并运行骨架
python3 scripts/lab.py run sum --all   # 跑本机所有能跑的目标，并比对输出是否一致（目前只在 Windows 上实测过）
```

开发时直接打开某一节（截图、冒烟用，界面上不暴露）：环境变量 `ATHENA_MACHINE_OPEN=<章 id>/<知识点 id>`，
例如 `AsmBasics/machine.asm.basics.registers`；只写章 id 就停在该章大纲。

不要把产物装进 `/Applications`，也不要把 LVGL 小程序当成教学入口。

## 编写教案和出题

写新节的顺序：**打开本地教材对应文件 → 用 C23 / N3220 核对该条是否仍真 → 写 QML → 按同一节出题。**

1. **首页只画章。** 节点是 `chapters[]`，箭头是 `prerequisites`，边框配色是章的难度，
   卡片上的标签是章所在的线（`track`）。C 侧主干仍是 Beej 的
   `内存与变量 → 指针 → 数组 → 字符串 → 结构体 → 动态分配`，另有「控制流」「函数」两章为汇编线铺垫。
   灰章是还没有写成的教案，仍可点进大纲。不按 C23 特性清单另开一章。
   新章的 `difficulty` 先写 0（未评），写出内容之后才评定；`source_refs` 先留空，来源进 catalog
   之后随知识点一起补。
2. **点章进入大纲**，大纲只指方向：一句题注 + 五节（痛点、模型、边界、判断、落点）。
   节叫什么由本章知识点决定。知识点路线图画在「先看主次与顺序」里，点白卡片进教案。
3. **各节教学过程**写在 `qml/lessons/`：正反例、内存条、callout、先猜再看。
   不要把大纲五段再贴进每一节。概念对照、技能变式，按知识类型选，不要三类同一套模板。
4. **随堂考核和课后习题**写在 `exercises.json`，按知识点 ID 挂上。每题默认带
   `source_refs`，每条写齐 `relation`（与原材料的关系）、`source_id`（catalog 里的
   来源）、`locator`（教材节号 + 必要时 `c23` 条款）——字段名是跨应用统一的那套
   （主仓库 ADR 0043 第 1 节）。题干用中文改写该节事实，不整段抄 NC-ND 正文，
   所以关系一般是 `adapted`；真照抄原句才用 `quoted`。教材与 C23 冲突时以 C23
   为准，两边都引用。对不上的题不要写。出处档位是 open（主仓库 ADR 0089）：漏标
   只报告不阻断，但不得为了省事伪造出处；已标的出处仍被逐条校验。
5. **实验台**打开 `playground/` 里保留的小程序（若已构建）；教案里的内存条是讲解，不是实验替代品。
   可运行示例默认 `-std=c23`。不拿 gnu17 的输出去否定 C23 教案。

知识点 ID 以 `machine.c.`、`machine.asm.` 或 `machine.joint.` 开头（ADR 0005）。篇幅跟 `difficulty` / `mastery_goal` 匹配。新章、新知识点、
新题都必须能在 `content/sources/catalog.json` 对上节号；语义对错以 C23 为准。
