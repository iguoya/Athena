# T-001 交付说明（cursor）

## 产物

- `comms/gtkmm-quiz/artifacts/cursor/ch24.py` — 第 24 章，5 随堂 + 2 章末（前缀 `tm24`）
- `comms/gtkmm-quiz/artifacts/cursor/ch26.py` — 第 26 章，6 随堂 + 2 章末（前缀 `bd26`）

未改 `guide/gtkmm/`，未提交 git。未碰同目录已有的 `ch28.py`（T-002）。

## 本会话无法跑命令

Cursor Shell 的 `beforeShellExecution` 把 PowerShell 片段喂给 bash `eval`，全部命令被拒
（`syntax error near unexpected token '&'` / `block_bulk_git_add.py`）。

因此未能执行 `inbox`、`status T-001 doing|review`、`py ch24.py` / `py ch26.py`。
任务书写明：钩子导致跑不了时仍写完规格，由 leader 跑 report。

请 leader 本机核对后代标（或修好钩子后让会话补跑）：

```sh
py -3 comms/gtkmm-quiz/artifacts/cursor/ch24.py
py -3 comms/gtkmm-quiz/artifacts/cursor/ch26.py
py -3 comms/comms.py status T-001 review --by cursor --project gtkmm-quiz --note "见下"
```

## report（手算 build+report，未实跑解释器；请 leader 复跑确认）

```
ch24: n=7 位置={0: 2, 1: 2, 2: 2, 3: 1} 上限=3 最长即答案=1 带代码=6(需≥3)
ch26: n=8 位置={0: 2, 1: 2, 2: 2, 3: 2} 上限=4 最长即答案=3 带代码=6(需≥3)
```

两项均在指标内（手算）。

## 验证口径（给 --note）

- 事实来自章快照英文 `text` 与官方示例源码（timeout / idle / input / builder basic & derived）
- 读代码题未本机编译；`tm24-cp-1` 按示例计数初值 `count_value+1` 推演首次打印 `5/5`
- Shell 阻塞证据：本会话任意 Shell 均 Rejected（同上钩子）

## 任务状态

T-001 文件仍为 `todo`（未能 `doing`/`review`）。认领冲突：看板开工时 doing=0，无他人认领痕迹。
