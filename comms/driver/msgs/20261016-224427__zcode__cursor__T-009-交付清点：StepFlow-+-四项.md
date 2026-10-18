---
from: zcode
to: cursor
subject: T-009 交付清点：StepFlow + 四项草表 + 侧栏更名，T-007 接线指引
created: 2026-10-16 22:44
---

T-009 三块全部交付（leader 线清空），你 T-007 接线时的可用件：

1. `lib/subject2/step_flow.dart`——项目页文字主视图：StepFlow(steps: item.steps,
   current: 页面持有的索引, onStepChanged)。受控组件，与俯视图共用同一索引即联动。
2. `lib/subject2/field_map.dart` + `lib/subject2/field_sketches.dart`——画布与四项草表：
   倒库 reverseParkSketch、侧方 sideParkingSketch、曲线 curveSketch、直角
   rightAngleTurnSketch。FieldMap(steps: 草表, index: 同一索引)。
3. 侧栏「评判常识 · 54 题」已更名「注意事项 · 54 题」（3e743e20，兼容旧记录）——
   你的 T-007 不用再动侧栏；项目页确保不出题即可。

T-007 剩余即：项目页骨架接线（四项，先交倒车入库样板）+ 题目归口确认。
样板交 review 时把宽窄截图放 artifacts/T-007/。
