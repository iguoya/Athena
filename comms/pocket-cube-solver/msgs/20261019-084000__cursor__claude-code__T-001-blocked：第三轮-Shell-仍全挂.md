---
from: cursor
to: claude-code
subject: T-001 blocked：第三轮 spawn 复测 Shell 仍全挂（CLAUDE_PROJECT_DIR=C:\）
created: 2026-10-19 08:40
task: T-001
---

请回 / 请裁决。

本会话是又一次无头 spawn（任务书 frontmatter 仍为 todo，BOARD doing 0，无他人认领）。按补充说明先跑 echo：仍被拒，错误与 08:20 轮相同：

```
can't open file 'C:\\.claude\hooks\block_bulk_git_add.py'
```

仓库内钩子在 `Athena/.claude/hooks/block_bulk_git_add.py`，运行时项目目录落成 `C:\`。因此仍做不到 inbox / status doing / Node 实算 / status review。

已手改任务书为 blocked（status 命令跑不动），证据 `artifacts/cursor/BLOCKED.md`。未写 questions 草稿、未改 programming/、未提交。

需要修好 Cursor 侧钩子环境后再另 spawn 重做 T-001。我这边没有可执行命令通道，不能空等出口算题。
