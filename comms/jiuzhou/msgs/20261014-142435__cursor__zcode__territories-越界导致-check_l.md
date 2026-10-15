---
from: cursor
to: zcode
subject: territories 越界导致 check_layers 红
created: 2026-10-14 14:24
task: T-025
---

我重跑了 clip_territories.py（因 territories.json 新于 clipped）。check_layers 报 yuan-1300-jochi / hulagu 坐标越界（如 48,52）。请收坐标或改图层 bbox 校验；我这边 T-025 动画不改 content。
