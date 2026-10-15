---
id: T-901
title: 观察台应用本体：壳、数据层、三视图（leader 自领）
owner: zcode
status: done
priority: P0
depends: 
created: 2026-10-15 18:46
updated: 2026-10-15 19:17
---
## 目标

leader 自领（ADR 0166 决策 5）：观察台应用本体。

1. 壳：复制 certification/software（Tauri 2 + React + Tailwind），逐项改名
   id=comms-console、端口 1521、进程 athena-comms-console、数据目录 AthenaCommsConsole。
2. Rust 数据层：解析本地 comms/ 各舱（tasks/msgs/chat/config，含任务进展记录行）；
   PG（postgres crate）ingest 幂等投影 + 查询；PG 不可达/未配置降级直读文件。
3. React 三视图：看板泳道（按状态）、任务详情（任务书 + 流转时间线 + 关联消息）、
   对话流（正式消息 + 即时 chat 统一时间线、线程折叠）；附每舱活动统计（自绘 SVG）。
4. 四件套（AGENTS/CLAUDE/README/check.py）、icon.svg、登记与锁文件。

## 验收

- `python3 scripts/check.py comms-console` 绿（tsc + vite build + cargo check/test）。
- 打开应用能看到 comms/driver 与 comms/comms-console 两个真实舱的数据。

## 进展记录
- [2026-10-15 19:12] zcode：todo → doing · 本体已提交 f4fc4629，实机启动验证中
- [2026-10-15 19:17] zcode：doing → done · leader 自验：check 全绿（tsc/vite/cargo check+test）；launcher open 实机启动，截图确认看板泳道（driver 舱 4 任务、依赖等待标记）与对话流（线程折叠、leader 徽标、即时消息混排）渲染正确；修一个真 bug：CRLF 行尾让 front matter 解析整批失败
