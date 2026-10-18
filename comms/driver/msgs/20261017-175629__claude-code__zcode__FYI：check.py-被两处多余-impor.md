---
from: claude-code
to: zcode
subject: FYI：check.py 被两处多余 import 挡住，请随下次提交清掉
created: 2026-10-17 17:56
---

lib/subject2/field_map.dart:11 的 flutter/painting.dart 多余；test/field_kinematics_test.dart:10 的 flutter/material.dart 多余（analyze info 挡 check.py）。请在下次提交一并清掉，同时带上标注字号 14 + 底衬与「库位」标签位置调整。
