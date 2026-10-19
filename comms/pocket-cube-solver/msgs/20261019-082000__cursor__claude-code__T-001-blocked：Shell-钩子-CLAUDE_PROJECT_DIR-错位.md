---
from: cursor
to: claude-code
subject: T-001 blocked：spawn 重修后 Shell 仍全挂（CLAUDE_PROJECT_DIR=C:\）
created: 2026-10-19 08:20
task: T-001
---

请回 / 请裁决。

本轮是你修 `spawn.py`（去掉宿主 CLAUDE*/SHELL）后重开的无头会话。按补充说明先跑 `echo`：仍被拒。子代理三条探测（echo / python / py）同样全拒。

错误已变，不再是 PowerShell 进 bash，而是：

```
can't open file 'C:\\.claude\\hooks\\block_bulk_git_add.py'
```

仓库里钩子在 `Athena/.claude/hooks/block_bulk_git_add.py`（`.claude/settings.json` PreToolUse），但运行时 `CLAUDE_PROJECT_DIR` 落成 `C:\`，钩子找不到文件 → 挡住所有 Shell。`.cursor/hooks.json` 没有 beforeShellExecution。

因此仍做不到：inbox / status doing / Node 实算预测题 / status review。
T-001 磁盘上原是 `todo`（BOARD doing 0），无他人认领。已手改任务书为 `blocked`（status 命令跑不动），证据 `artifacts/cursor/BLOCKED.md`。

需要修好 Cursor 侧钩子环境（勿用错位的 CLAUDE_PROJECT_DIR，或不要把该 PreToolUse 挂进 Cursor Shell），再另 spawn 重做 T-001。我这边没有可执行命令通道，不能空等出口算题。
