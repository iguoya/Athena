# 协作观察台 — 项目协作规则

本文档是 **`tools/comms-console` 独立应用** 的项目级指令。本应用与仓库里其他应用
**平级、可脱离**：不读别人的配置、不链接别人的代码。

改本应用时以本文为准。目录 id 是 `comms-console`，进程 `athena-comms-console`，
端口 1521。工具类应用：不建进度库、不建出处契约，教学规范不生效（ADR 0146）。

## 定位

- **观察多智能体协作**：把 `comms/` 各舱的任务发布、状态流转、裁决、即时对话
  做成可打开就看的桌面界面（ADR 0165、0166）。它是「看」的工具，**只读**——
  不回消息、不改状态、不发任务；一切写操作走 `comms/comms.py`。
- 观察台的使用者是人和代理双方：代理干完活来这里看全景，人在这里监督代理。

## 架构（ADR 0166，改前先读）

1. **文件是唯一权威，PG 是投影。** 数据源永远是 `comms/<舱>/` 下的文件；
   路由器 PostgreSQL（库 `athena_comms`）只存投影，供多机汇聚查看。
   界面上必须标明当前数据来源（中心库 / 本地文件）。
2. **降级永远可用**：没配 DSN 或连不上 PG 就直读本地文件，不报错白屏。
3. **ingest 幂等**：按「舱 + 相对路径 + 内容哈希」去重；PG 里的表（bays / tasks /
   task_events / msgs / chats / sync_files）由 ingest 首次运行自动建（`CREATE TABLE
   IF NOT EXISTS`），结构变更走新增列或新表，不删列。
4. **单文件解析失败只跳过该文件**，不让整个快照失败——观察台宁可少显示一条。

## 技术栈

- **壳**：Tauri 2 + React + TypeScript + Tailwind（最初复制自
  `certification/software`，此后独立演进）；核心依赖写 `catalog:`，tauri / serde
  写 `workspace = true`，共享仓库根锁文件（ADR 0140）。
- **Rust 侧**：同步 `postgres` 驱动（投影与查询都是短批量操作）；DSN 从环境变量
  `ATHENA_COMMS_PG` 或用户数据目录 `AthenaCommsConsole/pg.json` 读，不进仓库。
  仓库根定位：环境变量 `ATHENA_COMMS_CONSOLE_ROOT` > 从进程 cwd 逐级向上找
  `comms/comms.py`。
- **界面**：中文；亮色纸面基调，品牌色青绿（`--color-brand-*`，styles.css 的
  `@theme`）；图标只用 `lucide-react`，不引图表库（统计自绘 SVG）。
- 不引入 WebView 之外的重前端框架；不写自动刷新轮询——重开窗口或后续按需加
  手动刷新，实时推送总线明确不做（ADR 0166「不做的」）。

## 目录

| 路径 | 职责 |
|---|---|
| `src/` | React 界面：App（舱选择 + 视图切换）、`views/` 四视图（看板 / 任务与决策 / 对话流 / 活动统计）、`types.ts`（与 Rust 结构镜像） |
| `src-tauri/` | Rust：文件解析（front matter、任务进展记录行、chat 行）、PG ingest 与查询、降级 |
| `app.json` | 怎么构建、怎么启动、怎么算就绪 |
| `docs/decisions/` | 本应用 ADR（如有） |
| `scripts/check.py` | 本应用验证入口 |

## 协作（本应用自己就建在 comms 机制上）

本应用由 `comms/comms-console/` 舱协作开发（leader=zcode 主会话，worker=zcode-2
与 cursor）。改代码前先跑 `python comms/comms.py inbox <名字> --project comms-console`；
文件归属见该舱 README。

## 开发与验证

```sh
launcher open comms-console        # 打开（启动器按 app.json 编译并拉起）
python3 scripts/check.py           # 结构校验 + 前端 tsc/vite 构建 + cargo check/test
python3 scripts/check.py --skip-rust   # 只改了前端时
```

改 `src/` 热重载；改 Rust 要重启 dev。icon.svg 改完跑
`.cache/cargo-target/release/launcher icons` 重新生成位图。
