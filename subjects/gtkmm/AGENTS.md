# Athena GTKMM — 项目协作规则

本文档是 **`subjects/gtkmm` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建、学习与实验全流程。仓库根 `AGENTS.md` 写各应用共同遵守的规则；
**改本应用时以本文为准**。

## 定位

- 目标：以**理论文档为主体**学 gtkmm（GTK4 的官方 C++ 绑定）——实践是理论的
  具象化演示，不是相反。讲解、交互模拟、真机演示、可编辑实验统一在一个软件里，
  每个演示有明确目的与所属理论点。
- 内容基准与资料分层见 [docs/decisions/0002](docs/decisions/0002-translation-baseline-and-source-layers.md)
  与 [docs/decisions/0003](docs/decisions/0003-migration-chapters-return-to-mainline.md)：
  官方教程《Programming with gtkmm 4》全量翻译为编排基准（GFDL，义务三件套见
  声明页）；`docs.gtk.org/gtk4` 是语义基准；gtk4-demo 与 gtkmm-demo（GNOME/gtkmm
  仓库 `demos/gtk-demo/`）入参考层。
- 章节编号与排序**严格跟随官方文档**（主线 = 官方第 1–31 章，含第 4、5 章版本
  迁移；参考层 = 第 32 章与附录 A–H），不做任何局部调整（应用 ADR 0003）。
- **学习方法原型（ADR 0113）**：主原型**预测–运行**，辅**真做校验**。先预测界面效果（布局结果、信号触发顺序）再运行，可编辑实验真编译校验。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust）
- **界面**：Vite + React + TypeScript + Tailwind + motion（参照拾阶体系）
- **原生侧**：每个演示与实验一个独立 CMake 工程（`gtkmm-4.0`，C++17，
  Windows 用 MSYS2 工具链），编译产物由壳 spawn，协议见下
- **内容**：`content/curriculum.json`（课表）+ `content/demos.json`（演示/实验
  清单）+ 章节翻译正文（本目录唯一内容源）
- **进度**：SQLite，写本应用自己的库（`progress/learning.db`，随仓库走，
  主仓库 ADR 0053）；知识点 ID 前缀一律 `gtkmm.`
- 出处默认标注（主仓库 ADR 0043；档位 open，ADR 0089，只报告不阻断）：题面指向
  `docs.gtk.org` 或教程章节，演示观察题指向演示条目；不凭印象伪造出处

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表、演示/实验清单、章节翻译；**唯一内容源** |
| `demos/` | 演示与实验的 CMake 工程骨架（只读，学习者副本在工作区） |
| `workspace/` | 学习者工作集：骨架实验的学习者副本与自由学习测试项目（个人区，不进清单与统一构建，构建产物不入库） |
| `src/` | 前端：导航、讲解、模拟、测验 |
| `src-tauri/` | 窗口、读内容、进度、spawn/协议转发 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `launcher` 执行 |
| `docs/decisions/` | 本应用 ADR |
| `AGENTS.md` | 本文 |

## 内容与教学分层

- **块类型承载一切讲解**（主仓库 ADR 0058）：正文、代码、要点、交互模拟、演示卡、
  实验卡、观察题、随堂测验、章末 checkpoint；不为某章手写整页。
- **左侧目录分三区**：教程章节（原文翻译，主线，官方第 1–31 章）、实验（与教程
  章节并列的独立入口，条目引用 `demos.json` 实验实体 id，按组聚合）、参考
  （贡献指南与附录，完整呈现但不进学习主线）。知识点内的实验卡是随堂入口，
  实验区是聚合总览；两者引用同一份实体，不产生第二事实源。
- **模拟与真机演示强制配对**（应用 ADR 0001）：每个 Web 交互模拟必须在
  `content/demos.json` 登记对应的演示 id；没有真机锚定的模拟不上线。模拟行为
  以语义基准校准，简化处在界面上标明。
- **演示粒度**：一理论点一演示，目标 ≤150 行、可通读；演示源码即教材。
- **骨架实验**（主仓库 ADR 0059）：`CMakeLists.txt` + `src/main.cpp` 骨架不改
  一行也能编译运行；学习者只补 TODO 标注区；骨架只读，副本在工作区，可重置。
- **完成度**：只由随堂测验与章末 checkpoint 作答按正确率写入；演示观察题计入
  同一回路。禁止手动「标记熟练」。
- 课表块引用清单 id，清单是壳、check、宿主三方的唯一事实源。

## 上游追踪（段落级，严格跟随官方仓库）

- 官方仓库克隆在 `upstream/gtkmm-documentation`（gitignore，不入库）；基准记录在
  `upstream.json`（url、分支、pinned_commit、docbook 路径）。文档源是
  `docs/tutorial/C/index-in.docbook`（单个 DocBook），官网「每节一页」由 XSLT
  生成，**分页单元 = 章下第一层 `<section>`**。
- **原文不手写**。每节的段落快照 `content/chapters/<章 xml:id>/<节 xml:id>.json`
  由 `scripts/sync_upstream.py` 从上游 DocBook 生成并入库：`blocks[]` 是有序段流
  （para/listitem/code/heading/figure），每段带指纹（sha256）与 `zh`（中文翻译，
  唯一的手写内容）。上游一变，git diff 直接显示哪一段变了。
- **结构不许自由发挥**：章/节 id、顺序、分页一律来自官方；课表 `sections[].pages`
  的节集合必须与官方完全一致（check 校验：缺页、多页、改名都报错）。
- **同步流程**：`git -C upstream/gtkmm-documentation fetch`（需要时 checkout 新
  commit）→ 跑 `sync_upstream.py`——按段落指纹做 LCS 对齐：指纹相同的段自动保留
  译文；原文被改的段标 `stale`（旧译文存 `stale_from` 供参考）；新增段标
  `untranslated`。**只译 stale/untranslated 的段**，译完清掉状态字段 → 在
  `upstream.json` 更新 `pinned_commit`，一个上游版本一个提交。
- **代码与代码语句永远原样**：官网文档中的代码块、行内代码、命令一律逐字提取
  （`code_text()` 只还原 XML 实体、剥标签，保留缩进与内部空白），不翻译、不注释、
  不改写；快照 code 块的 `zh` 恒为空，前端代码块不显示译文。手写知识点里的代码
  示例是原创教学内容，不属此约束。
- 课表页的 `translated` 状态要求该节快照里全部文字段都有 `zh`（check 校验一致性
  与 pinned_commit 版本）；语义争议以官方 DocBook 当前内容为准，官方 zh_CN.po
  可作术语参照（覆盖率不完全）。

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
