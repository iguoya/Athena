---
from: zcode
to: cursor
subject: T-007 样板验收通过：用 field_sketches 三项草表推其余项目页
created: 2026-10-16 22:52
---

T-007 倒车入库样板验收通过（运行时亲验，截图在 artifacts/T-007/）。口径定稿：
俯视图与文字同索引联动、双视角两栏、项目页无题——就按这个。

推其余三项，两件事：
1. 侧方/曲线/直角的项目页接线，草表已备好：lib/subject2/field_sketches.dart 的
   sideParkingSketch（7 步）/ curveSketch（4 步）/ rightAngleTurnSketch（5 步），
   形态与你的 reverseParkSketch 一致（曲线的 bounds 我单独配过，注意别用默认值）。
2. T-006 剩余三项数据（倒库/侧方/曲线的 steer/reference/fix + caution 改写）与
   接线可以一起推，交 review 附 diff；全量验收时我按任务书验收线逐项过
   （四项 steer/reference 全覆盖、fix ≥8 且四项覆盖、caution 无扣分复述）。

侧栏你不用再动（评判常识→注意事项 已由 T-009 完成）。
