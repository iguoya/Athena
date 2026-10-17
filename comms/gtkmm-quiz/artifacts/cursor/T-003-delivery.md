# T-003 交付说明（cursor）

## 产物

- `comms/gtkmm-quiz/artifacts/cursor/ch18.py` — 第 18 章 DrawingArea/Cairo，8 随堂 + 2 章末（前缀 `da18`）
- `comms/gtkmm-quiz/artifacts/cursor/ch27.py` — 第 27 章国际化，7 随堂 + 2 章末（前缀 `in27`）

未改 `guide/gtkmm/`，未提交 git。未碰同目录已有的 ch24/ch26/ch28/ch29。

## 本会话无法跑命令

Cursor Shell 的 `beforeShellExecution` 把 PowerShell 片段喂给 bash `eval`，全部命令被拒
（`syntax error near unexpected token '&'` / `block_bulk_git_add.py`）。

因此未能执行 `inbox`、`status T-003 doing|review`、`py ch18.py` / `py ch27.py`。
任务书写明：钩子导致跑不了时仍写完规格，由 leader 跑 report。

请 leader 本机核对后代标（或修好钩子后让会话补跑）：

```sh
py -3 comms/gtkmm-quiz/artifacts/cursor/ch18.py
py -3 comms/gtkmm-quiz/artifacts/cursor/ch27.py
py -3 comms/comms.py status T-003 review --by cursor --project gtkmm-quiz --note "见 T-003-delivery.md"
```

## report（手算 build+report，未实跑解释器；请 leader 复跑确认）

```
ch18: n=10 位置={0:2, 1:3, 2:3, 3:2} 上限=4 最长即答案≈0~2（写时压过 cp-1） 带代码=8(需≥4)
ch27: n=9  位置={0:2, 1:2, 2:3, 3:2} 上限=4 最长即答案≈0~2（写时压过 help-1、cp-1） 带代码=5(需≥3)
```

两项均按指标手算；选项长度请以本机 `report()` 为准。

## 覆盖与取舍

- 第 18：drawing-model / lines / curved / arcs / text / images 各有随堂；clock 合入章末 `da18-cp-1`（任务允许少数页合并）。
- 第 27：六节各 ≥1 随堂；前缀按任务用 `in27`（不用 `i1827`）。
- 事实以章快照英文 `text` 与内嵌示例为准；细线题按英文「像素中间 / m_fix=0.5」。
- 读代码题未本机编译；结论均可从原文或示例源码直接推出。

## 任务状态

T-003 文件仍为 `todo`（未能 `doing`/`review`）。看板开工时无他人 doing 痕迹；本会话为 spawn 指定的 T-003 无头会话。
