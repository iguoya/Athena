# Athena · 数据结构与算法（独立应用）

与主程序**平级**的独立学习应用（ADR 0032）。技术栈自选：Tauri 2 + Web UI +
本机 C++ 工具链。主程序首页图谱上的「数据结构与算法」节点只负责把它拉起来；
**不启动主程序也可以完成全部学习业务**。

## 设计原则

1. **业务自足**：课程内容、进度、实验编译运行全在本目录闭环。
2. **内容驱动**：`content/curriculum.json` 是唯一课表；UI 只做渲染与互动。
3. **实验真源码**：`content/cases/` 里是可编辑的 C++；保存后本机编译运行。
4. **主程序可选**：有 `--store` 时写入共用学习库；没有则用本应用自己的 SQLite。

## 架构（与 GTK 主程序无关）

```
content/          课表、教案块、C++ 案例（唯一内容源）
src/              前端：导航 + 导览/大纲/讲解/实验
src-tauri/        壳：读内容、进度库、compile_and_run
bin/athena-dsa    构建产物入口（给主程序 discover）
```

页面结构（精神对齐主程序学习页，布局按 Web 重做）：

- **左侧**：章 → 知识点（难度 / 掌握目标徽章）
- **右侧四栏**：本章导览 · 教学大纲 · 讲解 · 实验
- **实验三栏**：源码编辑 · 编译/输出 · 观察区（框架版占位，后续接可视化）

## 构建与运行（完全独立）

依赖：Node.js、Rust（rustup）、本机 `c++`/`clang++`，以及系统 `sqlite3`（pkg-config）。
**不需要**先开 Athena。协作规则见 [`AGENTS.md`](./AGENTS.md)。

```sh
# 推荐：开发（自动补 PATH）
./scripts/dev.sh

# 或手动
export PATH="/usr/local/opt/node/bin:/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"
cd apps/dsa
npm install
npm run tauri:dev
```

发行 / 给 Athena 首页点击用：

```sh
cd apps/dsa
npm install
LIBSQLITE3_SYS_USE_PKG_CONFIG=1 npm run build:app
./bin/athena-dsa              # 独立窗口；macOS 会保留并启动完整 .app
```

构建成功后会生成稳定入口 `bin/athena-dsa`；macOS 入口转发到保留完整上下文的
`bin/athena-dsa.app/Contents/MacOS/athena-dsa`，其他平台转发到本机可执行文件。
Athena 首页点「数据结构与算法」会 spawn 这个稳定入口，并透传共用学习库路径
（需使用已编入 ExternalApp 入口的主程序，例如 `builddir/Athena`）。

## 内容怎么规划（当前课表）

四条学习带，图谱按 `requires` 自动分层：

1. **度量与线性**：大 O → 时间 / 空间 / 摊还 → 数组 → 链表 → 栈队列  
2. **关联与层次**：哈希表 → 树遍历 → BST → 堆  
3. **排序与图**：基础排序 → 高效排序 / 二分 → 图表示 → 遍历 → 最短路径入门  
4. **解题范式**：分治 → 贪心 → DP → 回溯  

相对旧主程序 `da` 分类的调整：补上**哈希表**主线；砍掉几何 / 数论等边缘章；最短路径标为 familiar；范式放在结构之后。

首页是**可点知识图谱**（仿 C++ 分类图谱：白卡片、主色描边、先修边）；点节点进入导览 / 大纲 / 讲解 / 实验。

## 目录

| 路径 | 内容 |
|---|---|
| `content/curriculum.json` | 章与知识点元数据、导览/大纲/讲解块 |
| `content/cases/` | C++ 实验源码 |
| `src/` | 前端 |
| `src-tauri/` | Tauri / Rust 命令 |
| `app.json` | 仅供主程序发现；本应用不依赖它才能跑 |
