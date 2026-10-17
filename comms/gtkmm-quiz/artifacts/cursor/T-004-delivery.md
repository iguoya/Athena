# T-004 交付说明（cursor）

## 产物

- `comms/gtkmm-quiz/artifacts/cursor/ch19.py` — 第 19 章，6 随堂 + 2 章末（前缀 `dn19`）
- `comms/gtkmm-quiz/artifacts/cursor/ch20.py` — 第 20 章，5 随堂 + 2 章末（前缀 `cl20`）
- `comms/gtkmm-quiz/artifacts/cursor/ch21.py` — 第 21 章，7 随堂 + 2 章末（前缀 `pr21`）

未改 `guide/gtkmm/`，未提交 git。未碰同目录已有的 ch24/ch26/ch28/ch29。

## 本会话无法跑命令

Cursor Shell 的 `beforeShellExecution` 把 PowerShell 片段喂给 bash `eval`，全部命令被拒
（`syntax error near unexpected token '&'` / `block_bulk_git_add.py`）。

因此未能执行 `inbox`、`status T-004 doing|review`、`py ch19.py` / `ch20.py` / `ch21.py`。
任务书写明：钩子导致跑不了时仍写完规格，由 leader 跑 report。

请 leader 本机核对后代标（或修好钩子后让会话补跑）：

```sh
py -3 comms/gtkmm-quiz/artifacts/cursor/ch19.py
py -3 comms/gtkmm-quiz/artifacts/cursor/ch20.py
py -3 comms/gtkmm-quiz/artifacts/cursor/ch21.py
py -3 comms/comms.py status T-004 review --by cursor --project gtkmm-quiz --note "见 T-004-delivery.md"
```

## report（模拟 build+report，未实跑解释器；请 leader 复跑确认）

首轮模拟（压短前）已过线但 ch20 最长即答案=3 贴上限。已再压短
`dn19-ex-1`/`cp-1`、`cl20-fm-1`/`pa-1`/`ex-1`、`pr21-as-1`/`cp-1` 的正确项。

压短后预期（位置/代码题不变）：

```
ch19: n=8 位置={0:2, 1:2, 2:2, 3:2} 上限=4 最长即答案≤2 带代码=4(需≥3)
ch20: n=7 位置={0:2, 1:2, 2:2, 3:1} 上限=3 最长即答案≤1 带代码=3(需≥3)
ch21: n=9 位置={0:2, 1:3, 2:2, 3:2} 上限=4 最长即答案≤1 带代码=6(需≥3)
```

请以本机 `py -3 …/chN.py` 的 `report()` 为准。

## 节页覆盖

- ch19：四节各 ≥1 随堂（st/me×2/sig×2/ex）+ 2 综合
- ch20：四节各 ≥1（fm×2/co/pa/ex）+ 2 综合
- ch21：7 随堂覆盖 printoperation / page-setup / rendering-text / async / export-pdf / preview / printdialog；`sec-extending-print-dialog` 与 `sec-printing-examples` 并入章末综合（任务书允许合并少数页）

## 验证口径（给 --note）

- 事实来自章快照英文 `text` 与官方示例（dndwindow / clipboard simple+ideal / printing simple+custom tab）
- 读代码题未本机编译；结论按原文与示例源码推演
- 术语：部件、Cairo 保留原文
- Shell 阻塞证据：本会话任意 Shell 均 Rejected（同上钩子）

## 任务状态

T-004 文件仍为 `todo`（未能 `doing`/`review`；`tasks/` 归 leader，不手改 frontmatter）。
认领冲突：看板开工时 doing=0，无他人认领痕迹。
不确定点：请 leader 实跑 report 确认「最长即答案」计数；第 21 章两页合并是否接受。
