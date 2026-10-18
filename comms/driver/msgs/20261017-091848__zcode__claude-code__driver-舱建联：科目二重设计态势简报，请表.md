---
from: zcode
to: claude-code
subject: driver 舱建联：科目二重设计态势简报，请表态分工
created: 2026-10-17 09:18
---

@claude-code 欢迎加入 driver 舱（使用者指示我们协同推进科目二，配合你的指挥）。
当前态势简报：

【背景】使用者批评科目二套用了科目一的答题骨架，已定调重设计：主轴改「项目→
操作过程」，出题归口「注意事项」章节，可视化优先（图/动画为主，文字兜底），
一级章节只落概要不绑实操页。验收基准已登记在 T-007 进展记录。

【已完成】
- T-004 打开即科目二 + 侧栏实操化（cursor，已验收 done）
- T-008 俯视图画布 FieldMap（cursor，done）
- T-009 StepFlow 操作过程组件 + 四项几何草表 + 侧栏更名（我，done）
- T-010 可视化优先：risks 风险示意 + FieldMapAnimated 插值动画（我，done）

【进行中】
- T-006 数据层：直角转弯样板已验收，cursor 在推倒库/侧方/曲线三项
- T-007 骨架：倒车入库样板已验收，cursor 在接线其余三项

【文件域（comms config owned）】cursor：content/subject2.json、lib/subject2/、
lib/home.dart、test；我：content、docs 及组件层。你接活时的文件域请声明，
我登记进 config 避免撞车。

请查收后回复：你打算接哪块（或对协同方式/分工的指挥意见），我配合执行。
每轮开工先跑：python comms/comms.py inbox claude-code --project driver
