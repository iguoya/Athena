# Athena C — 项目协作规则

本文档是 **`subjects/c` 独立应用** 的项目级指令，不依赖任何其他应用。改本应用时以本文为准。

## 定位

- 目标：把 C 语言教成「看见内存」——字节有地址，指针存的是地址。章序跟
  Beej / DIS（ADR 0002 / 0003），**语义以 C23 为准**（ADR 0004）。
- **教案用 QML 写**（ADR 0042），不是启动一个演示用的 C 程序。
- 原 LVGL 小程序保留在 `playground/`，需要时单独构建，**不是**图谱入口。

## 教学结构

知识图谱节点是**章**，不是知识点。点进一章之后，大纲里才有该章的知识点路线图；教案从那张图
点进来。

| 层 | 本应用 |
|---|---|
| 知识图谱 | 首页六章 + `prerequisites` |
| 教学大纲 | 点章之后：方向 + 知识点路线图 |
| 教学过程 | 章内路线图点白卡片才进入 |
| 教学实验 | 实验台拉起 `playground/` |
| 随堂考核 | `Checkpoint.qml` + `exercises.json`：多题、有解析 |

章序跟 Beej 教程卷，节标题按 C 自己的内容取；只讲 C 的语义，引用、RAII、模板这类别的语言
特有的内容不在本应用里讲。

C 自己发挥的是内存条、地址箭头、playground 里真实的 C 程序。这些只让教材里
的命题被看见，不得发明一条教材没有的规则（例如把本机小端写成 C 的保证）。

## 技术栈

- **壳**：Qt 6 Quick / Qml（C++20）
- **教案**：`qml/lessons/*.qml` + 共用组件 `qml/components/`
- **课表**：`content/curriculum.json`（章、先修、难度、指向哪份 QML、`source_refs`）
- **题库**：`content/exercises.json`（随堂 / 课后，每题带 `source_refs`）
- **进度**：后续自建库，前缀 `c.`（ADR 0037），位置按 ADR 0053 放
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
| `playground/` | 保留的 LVGL 小程序，不从图谱启动 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `launcher` 执行（ADR 0046） |

## 开发

```sh
cd subjects/c
launcher open c
```

改 QML / `curriculum.json` / `exercises.json` 保存后窗口会自己重新加载。只有改
`src/` 才需要让脚本再编一次 C++。本机需要 Qt 6（Homebrew `qt@6`）。

不要把产物装进 `/Applications`，也不要把 LVGL 小程序当成教学入口。

## 编写教案和出题

写新节的顺序：**打开本地教材对应文件 → 用 C23 / N3220 核对该条是否仍真 → 写 QML → 按同一节出题。**

1. **首页只画章。** 节点是 `chapters[]`，箭头是 `prerequisites`，配色是章的难度。
   主干是 Beej 的 `内存与变量 → 指针 → 数组 → 字符串 → 结构体 → 动态分配`。
   灰章是还没有写成的教案，仍可点进大纲。不按 C23 特性清单另开一章。
2. **点章进入大纲**，大纲只指方向：一句题注 + 五节（痛点、模型、边界、判断、落点）。
   节叫什么由本章知识点决定。知识点路线图画在「先看主次与顺序」里，点白卡片进教案。
3. **各节教学过程**写在 `qml/lessons/`：正反例、内存条、callout、先猜再看。
   不要把大纲五段再贴进每一节。概念对照、技能变式，按知识类型选，不要三类同一套模板。
4. **随堂考核和课后习题**写在 `exercises.json`，按知识点 ID 挂上。每题必须有
   `source_refs`，每条写齐 `relation`（与原材料的关系）、`source_id`（catalog 里的
   来源）、`locator`（教材节号 + 必要时 `c23` 条款）——字段名是跨应用统一的那套
   （主仓库 ADR 0043 第 1 节）。题干用中文改写该节事实，不整段抄 NC-ND 正文，
   所以关系一般是 `adapted`；真照抄原句才用 `quoted`。教材与 C23 冲突时以 C23
   为准，两边都引用。对不上的题不要写。**漏标会让检查直接失败**（`blocking: true`）。
5. **实验台**打开 `playground/` 里保留的小程序（若已构建）；教案里的内存条是讲解，不是实验替代品。
   可运行示例默认 `-std=c23`。不拿 gnu17 的输出去否定 C23 教案。

知识点 ID 以 `c.` 开头。篇幅跟 `difficulty` / `mastery_goal` 匹配。新章、新知识点、
新题都必须能在 `content/sources/catalog.json` 对上节号；语义对错以 C23 为准。
