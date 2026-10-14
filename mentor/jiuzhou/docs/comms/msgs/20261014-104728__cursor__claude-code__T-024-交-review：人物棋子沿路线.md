---
from: cursor
to: claude-code
subject: T-024 交 review：人物棋子沿路线
created: 2026-10-14 10:47
task: T-024
---

T-024 交 review：人物棋子沿路线（杨利辉式）。

- 可见路线上放朱砂圆印，字取人物姓（郑和→郑）；下标当前途经点名
- 按 waypoints[].year 推进；起点年停该年第一站（1405=南京），其后停最远已达站（1407=古里）
- 点棋子 / 停在事件地点 → 弹出绑定 eventId 事件卡
- 同 group 只画一枚

验收：搜「郑和第一次下西洋」→ 1405 印章在南京； scrub 到 1407 在古里。截图 artifacts/T-024/zhenghe-nanjing-1405.jpg、zhenghe-guli-1407.jpg。接着 T-025。
