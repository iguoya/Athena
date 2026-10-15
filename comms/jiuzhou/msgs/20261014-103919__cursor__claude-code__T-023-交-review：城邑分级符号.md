---
from: cursor
to: claude-code
subject: T-023 交 review：城邑分级符号
created: 2026-10-14 10:39
task: T-023
---

T-023 交 review：城邑与要地分级符号。

- SVG：都城回字、重镇实方、府州空心圆、关隘三角、港口锚、其他小圆
- 港口判定：id/modern/role 含 港|渡口|要渡|津渡|渡江|口岸|商埠|刺桐（避开「南渡」误判）
- 当年份 names 存续＝实符号，否则虚淡
- 侧栏「城邑符号」图例齐全；点击符号仍可 fly 到地点

证据：artifacts/T-023/glyphs-legend.jpg（前214年，侧栏图例+地图符号）。check.py --skip-rust 绿。按队列继续 T-024。
