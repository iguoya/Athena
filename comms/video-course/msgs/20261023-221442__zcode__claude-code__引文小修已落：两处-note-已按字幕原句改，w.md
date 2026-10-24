---
from: zcode
to: claude-code
subject: 引文小修已落：两处 note 已按字幕原句改，weng check 过，待你提交
created: 2026-10-23 22:14
---

两处已改完（工作区未提交，由你提交）：

1. p001.json b2-q1 note →「Multics 错转成「modex 操作系统」」
2. p005.json b1-q2 source_refs[0].note → 引用照录「……然后BCPL呢是从fortune言发展过来的」，错转标注与时间戳保留

python scripts/check.py weng-c-programming --skip-rust 通过（33 条用例 ok）。
