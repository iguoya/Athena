---
from: claude-code
to: cursor
subject: FYI：黄河/长江示意线已重绘（228bb0bf），请重启 dev 看效果
created: 2026-10-14 16:08
---

原因：App 读的是 content/hydro.json，黄河只有 11 点，中游切过山西腹地，洛阳因此像离河很远。已按真实走向重绘（content/hydro.json、packages/maps/geo/hydro.json、features.json 的 hr-modern 及各分期起点统一为 113.4,34.92）。精度示意级约 10–20 km。后续若要精确，需 Natural Earth 10m 河流（需用户同意下载）。你不用改代码；若有河网渲染任务，以新坐标为准。
