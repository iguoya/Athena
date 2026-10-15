---
from: cursor
to: claude-code
subject: T-027 交 review：resize + 快照 fitBounds
created: 2026-10-14 08:49
task: T-027
---

T-027 交 review。

【改动】mentor/jiuzhou/src/App.tsx
1. ResizeObserver 挂在地图容器 → map.resize()；onLoad 再 resize 一次
2. 有 snapshot 时对 territoryData fitBounds（padding 56，maxZoom 5.2）；无快照才 flyTo 事件地点

【自测（dev :1516）】
- 容器缩到 640×480 后 canvas.clientWidth/Height 与容器一致（match=true）
- 前214：snaps=qin-215 territory=4；1279：snaps=yuan-1300[元,高丽,陈朝] territory=9
- 截图：%TEMP%/cursor/screenshots/page-2026-10-14T00-48-14-431Z.png 、page-2026-10-14T00-48-41-709Z.png
- check.py --skip-rust 绿
