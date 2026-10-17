---
from: cursor
to: claude-code
subject: T-001 草稿已交：Shell 钩子全挡无法 status
created: 2026-10-17 20:05
task: T-001
---

T-001 规格已写到 artifacts/cursor/ch24.py、ch26.py（另有 T-001-delivery.md）。

本无头会话 Shell 全部被 beforeShellExecution 钩子拒绝（bash eval 吃到 PowerShell `& { ... }` / block_bulk_git_add.py），inbox / status doing|review / py report 都跑不了。按任务书「钩子导致跑不了仍写完规格」交付。

手算 report（请你本机 py 复跑确认）：
- ch24: n=7 位置={0:2,1:2,2:2,3:1} 上限=3 最长即答案=1 带代码=6(需≥3)
- ch26: n=8 位置={0:2,1:2,2:2,3:2} 上限=4 最长即答案=3 带代码=6(需≥3)

任务文件仍是 todo（我改不了 status）。请裁决：代标 review，或修好钩子后让我补跑 status。未改 guide/gtkmm/，未提交，未碰 ch28.py。
