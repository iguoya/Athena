# Athena GTKMM — 项目协作规则

本文档是 **`subjects/gtkmm` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建、学习与实验全流程。仓库根 `AGENTS.md` 写各应用共同遵守的规则；
**改本应用时以本文为准**。

## 定位

- 目标：以**理论文档为主体**学 gtkmm（GTK4 的官方 C++ 绑定）——实践是理论的
  具象化演示，不是相反。讲解、交互模拟、真机演示、可编辑实验统一在一个软件里，
  每个演示有明确目的与所属理论点。
- 内容基准与资料分层见 [docs/decisions/0002](docs/decisions/0002-translation-baseline-and-source-layers.md)：
  官方教程《Programming with gtkmm 4》全量翻译为编排基准（GFDL，义务三件套见
  声明页）；`docs.gtk.org/gtk4` 是语义基准；gtk4-demo 与 gtkmm-demo（GNOME/gtkmm
  仓库 `demos/gtk-demo/`）入参考层。
- 只覆盖 **GTK4 / gtkmm-4.0**，不含 GTK3 迁移内容（迁移章节归参考层）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust）
- **界面**：Vite + React + TypeScript + Tailwind + motion（参照拾阶体系）
- **原生侧**：每个演示与实验一个独立 CMake 工程（`gtkmm-4.0`，C++17，
  Windows 用 MSYS2 工具链），编译产物由壳 spawn，协议见下
- **内容**：`content/curriculum.json`（课表）+ `content/demos.json`（演示/实验
  清单）+ 章节翻译正文（本目录唯一内容源）
- **进度**：SQLite，写本应用自己的库（`progress/learning.db`，随仓库走，
  主仓库 ADR 0053）；知识点 ID 前缀一律 `gtkmm.`
- 判分内容必须有出处（主仓库 ADR 0043）：题面指向 `docs.gtk.org` 或教程章节，
  演示观察题指向演示条目

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表、演示/实验清单、章节翻译；**唯一内容源** |
| `demos/` | 演示与实验的 CMake 工程骨架（只读，学习者副本在工作区） |
| `src/` | 前端：导航、讲解、模拟、测验 |
| `src-tauri/` | 窗口、读内容、进度、spawn/协议转发 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `launcher` 执行 |
| `docs/decisions/` | 本应用 ADR |
| `AGENTS.md` | 本文 |

## 内容与教学分层

- **块类型承载一切讲解**（主仓库 ADR 0058）：正文、代码、要点、交互模拟、演示卡、
  实验卡、观察题、随堂测验、章末 checkpoint；不为某章手写整页。
- **模拟与真机演示强制配对**（应用 ADR 0001）：每个 Web 交互模拟必须在
  `content/demos.json` 登记对应的演示 id；没有真机锚定的模拟不上线。模拟行为
  以语义基准校准，简化处在界面上标明。
- **演示粒度**：一理论点一演示，目标 ≤150 行、可通读；演示源码即教材。
- **骨架实验**（主仓库 ADR 0059）：`CMakeLists.txt` + `src/main.cpp` 骨架不改
  一行也能编译运行；学习者只补 TODO 标注区；骨架只读，副本在工作区，可重置。
- **完成度**：只由随堂测验与章末 checkpoint 作答按正确率写入；演示观察题计入
  同一回路。禁止手动「标记熟练」。
- 课表块引用清单 id，清单是壳、check、宿主三方的唯一事实源。

## 架构原则

- **独立可运行**：`launcher open gtkmm` 不经过任何别的应用。
- **内容驱动 UI**：改课优先改 `content/`，不为新节复制界面代码。
- **原生逻辑在 C++**：模拟只能画「模型」，GTK 行为的真相在演示与语义基准里；
  前端不另写一份行为权威。
- **协议与清单是不变量**（应用 ADR 0001）：JSON-RPC 2.0 over stdio（NDJSON），
  消息集 `initialize`/`shutdown`/`ping` ⇄ `ready`/`state`/`signal`/`log`；
  演示进程必须支持 `--self-check`（构造界面后退出 0）。演示宿主收编时
  协议与清单不动。
- **壳要薄**：Rust 侧负责路径、进程、进度与协议转发；业务文案与课树不进 Rust。
