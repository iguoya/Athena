# Athena DSA — 项目协作规则

本文档是 **`apps/dsa` 独立应用** 的项目级指令。本应用与 Athena 主程序
（GTK / Meson / `resources/athena.json`）**平级、可脱离**：不读主程序配置、
不链接主程序代码、不依赖主程序进程即可完成开发、构建、学习与实验全流程。

主仓库根目录的 `AGENTS.md` 只描述主程序与「异构应用」边界；**改本应用时以
本文为准**。可选地，主程序首页图谱可通过 `app.json` 把本应用当独立进程拉起
（ADR 0032），那不是运行本应用的前提。

## 定位

- 目标：数据结构与算法的学练合一——大纲指引方向，讲解落实细节，实验用
  **可即时编辑、本机编译运行的 C++** 验证预期，观察区后续承接可视化。
- 案例与讲解默认用 **C++20**；算法思想与语言无关，实现与对照以 C++ 为准。
- 不以做成在线 OJ 或通用 IDE 为目标；实验短小、可观察、可反复改跑。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust）
- **界面**：Vite + TypeScript（Web UI，非 GTK）
- **内容**：`content/curriculum.json` + `content/cases/**`（本目录唯一课表）
- **进度**：SQLite；**始终写入本应用自己的库**（用户数据目录下的
  `AthenaDSA/learning.db`），自建表、自迁移，不共用主程序的学习库，也不依赖
  主程序是否启动过（ADR 0037）。`--store` 仅为兼容旧版主程序而接受并忽略。
  知识点 ID 前缀一律 `dsa.`。
- **实验运行**：本机 `c++` / `clang++` / `g++`，`-std=c++20`，子进程编译运行
  （不是壳内 FFI）。

不引入主程序的 Meson、gtkmm、Blueprint、`athena.json`。

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表与 C++ 案例；**唯一内容源** |
| `src/` | 前端：导航、导览 / 大纲 / 讲解 / 实验 |
| `src-tauri/` | 窗口、读内容、进度、`compile_and_run` |
| `bin/athena-dsa` | 稳定入口脚本（给可选的主程序 discover） |
| `app.json` | 仅供主程序发现；本应用不依赖它才能开发或运行 |
| `AGENTS.md` | 本文；本应用协作规则 |

## 内容与教学分层

精神对齐「大纲 → 过程 → 实验」，载体与主程序无关。课表唯一源是
`content/curriculum.json`，可按学习建议重排章节与 `requires`。

当前推荐主线（详见 README）：

1. 复杂度与度量  
2. 线性结构（数组 → 链表 → 栈队列）  
3. 哈希表  
4. 树与堆  
5. 排序与二分  
6. 图  
7. 算法范式  

首页默认展示**按 requires 分层的知识图谱**；点节点进入四栏学习页。

## 架构原则

- **独立可运行**：`npm run tauri dev` / `./bin/athena-dsa` 不经过主程序。
- **内容驱动 UI**：改课优先改 `content/`，不为新节复制整页硬编码界面。
- **实验逻辑在 C++**：前端不重写一份算法真相；需要步进可视化时由 C++ 打印
  约定事件（如 NDJSON），前端只消费。
- **壳要薄**：Rust 侧负责路径、进程、进度；业务文案与课树不进 Rust。
- **与主程序零编译耦合**：主程序 Meson / `scripts/check.sh` 不构建本应用。

## C++ 实验约定

- 源码在 `content/cases/<case_id>/`，课表 `lab.case` / `lab.entrypoint` 指向它。
- 使用 `using namespace std;` 的偏好与主工程教学示例一致（可读优先）。
- `std::move` / `std::forward` / `std::remove` 始终带 `std::` 前缀。
- 实验宜短；编译失败时把诊断完整秀在输出区，不要吞掉。

## 开发与验证

```sh
cd apps/dsa
npm install
npm run tauri dev      # 日常开发（可热更新前端）
npm run build:app      # 产出 bin 入口可用的发行/本地二进制
./bin/athena-dsa       # 独立运行
./bin/athena-dsa --help
```

环境变量 `ATHENA_DSA_ROOT` 可强制指定应用根目录（含 `content/`）。

验证以本目录为准：前端 `npm run build`、Rust `cargo check`（在 `src-tauri`）、
以及至少一个 case 的编译运行。**不必**为改本应用而跑主仓库 `scripts/check.sh`，
除非同时改了主程序里的 discover / 图谱入口。

## 与 Athena 主程序的关系（可选）

- 主程序可通过扫描 `apps/dsa/app.json` 把本应用作为独立进程启动，不传任何状态。
- 图谱节点文案、是否挂入口，属于主程序仓库的改动；**本应用功能不依赖该入口**。
- 禁止为了「和主程序一致」而把课表迁回 `resources/athena.json`。

## 修改流程

1. 改课：先改 `content/curriculum.json` 与 cases，再补前端展示类型（若有新 block）。
2. 改运行时：只动 `src-tauri`，保持命令表面稳定。
3. 改 UI 布局：只动 `src/` + `index.html`，不反向要求主程序 UI 对齐。
4. 需要主程序入口时，另提主仓库变更（`domain_graph` / 文案），与本应用发版可分开。
