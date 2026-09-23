# ADR 0058：移除跨应用学科图谱首页，直接进入 C++ 知识图谱；「应用实践」分类搬出

- 日期：2026-09-22
- 状态：已接受
- 推翻：仓库级 ADR 0032 第 5–6 条、ADR 0044 第 8 条里「图谱入口保留不变」的结论
- 依赖：仓库级 ADR 0045（apps 平级）、ADR 0044/0046/0048（菜单栏启动器）

## 背景

`apps/cpp` 的首页原本是一张跨应用「学科路线图」：本地分类（C++）和 `apps/`
下的独立应用（dsa、english、mathematics、driver、polaris）画在同一张图上，
点哪个节点就进哪个应用。这个设计定型于 ADR 0032 第 5–6 条，ADR 0044 第 8
条在菜单栏启动器做出来之后又重申了一遍「图谱入口保留不变」——当时的理由是
「启动器不是学科导航」，两者回答的是不同问题。

但现在有了独立、常驻的 `launcher/`（菜单栏托盘 / macOS 菜单栏 /
`launcher open <id>`，ADR 0044/0046/0048），打开别的应用不再需要先开 cpp、再从首页
点出去。首页图谱当初要解决的问题——「怎么从一个入口找到所有应用」——已经
有了更专门的工具来做，图谱本身完成了阶段性任务。留着它，`apps/cpp` 就还在
扮演「异构应用集合的接待大厅」这个 ADR 0045 已经明确否定的角色（「C++ 教程
没有特权」）。

## 决策

### 1. 移除首页跨应用图谱，应用启动直接进 C++ 知识图谱

`apps/cpp` 现在只剩一个本地分类（C++；见下一条），不再需要一张「先选分类
还是选应用」的中间页。删除内容：

- `registry/domain_graph.h`/`.cc`（跨应用图谱的数据层）
- `render/domain_graph_view.h`/`.cc`（图谱的 Cairo 渲染）
- `ui/external_app_launcher.h`/`.cc`（发现并启动 `apps/` 下独立应用）
- `MainWindow` 里的 `home_page`/`home_graph`/`home_button`（`window.blp`）
  以及 `build_home_graph()`、`launch_domain_app()`、`go_home()`
  （`ui/mainwindow.cc`/`.h`）

`MainWindow` 构造完成后直接 `enter_category("cpp")`，`root_stack` 不再有
`"home"` 页，只剩 `"category"`（C++ 知识图谱与章节）和 `"experiment"`
（专注实验）。

### 2. 「应用实践」分类搬到 `apps/practice/`

首页图谱底下其实挂着两个本地分类，不止 C++：`practice`（应用实践，当前只
有一章「PocketCube 2 阶魔方」）教的是数据结构与算法思想（状态表示、旋转
操作），跟「C++ 语言本身」不是同一件事——`apps/cpp` 的边界一直是「教的是
什么，不是用什么语言写」（AGENTS.md），`practice` 不满足这条。

按 ADR 0045「一个目录一个独立单元，彼此平级」的精神搬出去，落点是
`apps/practice/`，跟 `apps/design-patterns` 一样先当材料坑——没有
`app.json`，没有 `scripts/check.py`，根验证入口按设计静默跳过。当前只是把
状态机、渲染代码、测试和 `.blp` 原样搬过去存着，技术栈和是否独立成一个
可运行应用留给以后真正接手时决定，不在本次决策范围内。

移走的文件：`practice/pocket_cube/{state,view}.{h,cc}`、
`practice/pocket_cube/pocket_cube.hpp`、`ui/pocket_cube_page.{h,cc}`、
`tests/pocket_cube_{state,view,}_test.cc`、
`resources/ui/chapters/practice_cube.blp`，以及 `resources/athena.json`
里的 `practice` 分类整段。

## 后果

**得到**：`apps/cpp` 打开即所见即所得——不再有一步「先看图谱、再进 C++」
的中间层；仓库级 ADR 0032/0044 里「图谱入口保留不变」的假设被推翻，两份
文件不改动原文（历史决策原样保留），但读者应该以本 ADR 为准。

**付出**：`apps/practice/` 现在是一堆脱离构建系统的静态文件，PocketCube
那一章的教学内容（2 阶魔方状态与旋转）从「能跑」退化成「能读」，直到有人
真正把它接成一个应用。这是本次决策的直接代价，不是失手。
