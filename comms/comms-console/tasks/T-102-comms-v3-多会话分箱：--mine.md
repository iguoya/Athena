---
id: T-102
title: comms v3 多会话分箱：--mine/--task 路由、已读分箱、认领冲突防护（ADR 0167）
owner: cursor
status: todo
priority: P1
depends: T-001
created: 2026-10-15 19:21
updated: 2026-10-15 19:21
---
## 目标

实现 ADR 0167（多会话并行：按任务分箱的收件路由）。使用者会开一个代理的多个标签页
并行多任务，现在收件箱混流、已读互踩、消息无地址。四件事：

1. **分箱**：消息带 `--task` 的进任务箱，无路由的进公共箱。已读游标从单文件
   `read/<名>.txt` 变为 `read/<名>.all.txt` + `read/<名>.<task>.txt`；旧的
   `read/<名>.txt` 存在就并入 .all 箱（兼容，不迁移删除）。
2. **过滤**：
   - `inbox <名> --mine`：公共箱 + 该名下所有 doing 任务的箱；
   - `inbox <名> --task T-xxx`：只看该任务箱（含历史）；
   - `ack <名> --task T-xxx | --mine`：写对应箱，互不影响；
   - `notify <名> [--mine]`：同过滤，供 hook 用——worker 会话只被「紧急 + 认领任务」
     打扰，其余静默。
3. **认领冲突防护**：`status T-xxx doing --by A` 时若当前已是 doing 且上次认领者
   不是 A，报错「该任务正在被认领（by B），请选别的任务或找 leader」——复用 v2 乐观锁。
4. **可选会话标记**：`status --as <短标记>`，写进流转行（`cursor(tab2)：todo → doing`）；
   缺省行为与文件格式完全不变。

## 做法

- 只改 `comms/comms.py` + `comms/tests/`；命令、文件格式向后兼容（旧舱、九州迁移后
  都能直接用）。
- 测试（comms/tests/ 里加 v3 用例）：分箱正确性；A 会话 ack 不影响 B 会话的箱；
  `--mine` 与认领状态联动；认领冲突被拦；`--as` 进流转行；旧单文件已读的并入。

## 验收

1. `python comms/tests/` 全部测试绿（输出摘要进 review note）。
2. 两个真实舱（driver、comms-console）`check` 通过，inbox 旧行为不变（不带新参数时）。
3. 演示：模拟两个会话（两个不同的 --task 各自 ack），一条消息只进一个箱——证据贴 review note。

## 依赖

- depends T-001（v2 原子写与乐观锁是地基，先落库）。

## 进展记录
