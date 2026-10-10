# Athena Python 与 AI 工具链 — 项目协作规则

本文档是 **`subjects/python` 独立应用** 的项目级指令，不依赖任何其他应用即可完成开发、
构建、学习与实验全流程。

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。启动器通过
`app.json` 把本应用当独立进程拉起（ADR 0032），那不是运行本应用的前提。

## 定位

- **学习应用**（主仓库 ADR 0120）：人工智能课程路线的第一门——面向**已经会编程**的
  人（软件/计算机背景）的 Python 与 AI 生态工具链。不教「什么是变量」，教的是：怎么用
  Python 把 AI 的活儿干起来。
- 承载：语法速成与 Python 惯用法、`uv` 环境与依赖管理、numpy/pandas 数据操作、
  HTTP 与 asyncio、Jupyter/notebook 工作流、项目工程化（测试、打包、脚手架）。
  它是 `machine-learning` → `deep-learning` → `llm-app` → `llm-finetune` 全线的地基
  （路线图见主仓库 ADR 0120）。
- **循序渐进的入口**：本应用没有先修；学完它之后，应用线直通 `llm-app`（大模型应用
  开发），原理线进 `machine-learning`。指引写在内容里，不引用对方路径或代码（ADR 0032）。
- **出处档位 open**（ADR 0089）：技术学习类，出处是默认习惯不做门禁——官方文档、
  PEP 与教程鼓励当场标注，未标注只报告不阻断；不凭印象伪造出处（要么如实标
  `authored`，要么不标），AI 现场出题不计入掌握度。
- **学习方法原型（ADR 0113）**：主原型**预测–运行**——脚本先预测输出再真跑对照，
  错误信息阅读是独立练习线；辅**真做校验**——每章收尾做一个真实的小工具（数据处理
  脚本、API 客户端、notebook 报告）。
- **实验形态**：实验在本机 Python 解释器真跑；应用只执行白名单内的预设命令，不提供
  任意 shell（ADR 0091 决策 3 同规）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），界面 React 18 + TypeScript + Vite。骨架阶段只有窗口与
  定位页；实验引擎（本机 `python`/`uv` 子进程真跑，白名单 spawn）随内容填充期落地，
  此后独立演进，不跟随任何应用（ADR 0062）。
- **内容**：`content/course.json`（本目录唯一课表）。
- **进度**：SQLite，写入本应用自己的 `progress/learning.db`（随仓库走，主仓库
  ADR 0053；发行副本退回用户数据目录 `AthenaPython/`），自建表、自迁移。
  知识点 ID 前缀 `python.`。
- 端口 **1505**（strictPort）；进程/二进制 `athena-python`。

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表与实验案例；**唯一内容源** |
| `src/` | 前端：导航、导读 / 讲解 / 实验 |
| `src-tauri/` | 窗口、读内容、进度、实验执行 |
| `app.json` | 声明怎么构建、怎么启动、怎么算就绪；由 `launcher` 执行（ADR 0046） |
| `scripts/check.py` | 本应用验证入口 |
| `docs/decisions/` | 本应用 ADR |
| `AGENTS.md` | 本文；本应用协作规则 |

## 内容与教学分层

- **内容驱动 UI**（ADR 0058）：讲解由块类型承载，不手写整页；骨架阶段的课表节全部
  `status: placeholder`，内容填充期替换。
- **随堂练习与考核**（ADR 0002）：完成度只由作答按正确率写入，禁止手动「标记熟练」；
  题量以覆盖本章知识点与典型误区为准，不凑数（ADR 0002、0096）。
- **实验给骨架**（ADR 0003）：脚本骨架 + `main` 驱动已备好，学员只补 `TODO`，
  不从零写整程序。
- 一节内容要有可提取物（ADR 0096）：每节至少一道「先预测再运行」或一个可跑的小工具。

## 判分与出处

- 题目鼓励当场标出处（官方文档、PEP、教程），如实标 `authored` 或不标；不凭印象
  伪造出处，AI 现场出题不计入掌握度（ADR 0043、0089 的 open 档约定）。

## 掌握度与激励(ADR 0052)

- 掌握度只由作答写入 `progress/learning.db` 的 `attempts`；激励只展示派生量，
  没有记录就没有徽章。

## 开发与验证

```sh
launcher open python
python3 scripts/check.py          # 骨架阶段默认结构校验
python3 scripts/check.py --full   # 追加前端构建与 cargo check
```

环境变量 `ATHENA_PYTHON_ROOT` 可强制指定应用根目录（含 `content/`）。

## 修改流程

1. 改课：先改 `content/course.json`，再补前端展示类型（若有新块）。
2. 改运行时：只动 `src-tauri`，保持命令表面稳定。
3. 改 UI：只动 `src/` 与 `index.html`。
