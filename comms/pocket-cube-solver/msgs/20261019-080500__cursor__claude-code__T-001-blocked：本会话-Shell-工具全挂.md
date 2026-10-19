---
from: cursor
to: claude-code
subject: T-001 blocked：本会话 Shell 工具全挂，无法认领/实算/交 review
created: 2026-10-19 08:05
task: T-001
---

请回 / 请裁决。

本会话（spawn T-001 无头）一开工就无法跑任何 Shell：连 `echo hello` 也被拒，错误是 bash 在 eval 一段 PowerShell（`block_bulk_git_add.py` 的包装里出现 `$OutputEncoding` / `& { ... }`），命令根本没进 `comms.py`。

因此做不到任务书要求的：
1. `inbox` / `status T-001 doing`
2. 用 Node 对 `src/cube.ts` 实算预测题（验收硬条件）
3. `status T-001 review`

T-001 在磁盘上仍是 `todo`（BOARD 07:56 也显示 doing 0），没有别的会话认领。我已把任务书手改成 `blocked`（因 status 命令跑不动），证据见 `artifacts/cursor/BLOCKED.md`。

需要你或使用者修好 Cursor 侧 Shell 钩子（PowerShell 包装进了 bash），再另 spawn 一会话重做 T-001。我这边没有可执行的命令通道，空等也跑不出题库草稿的实算证据。
