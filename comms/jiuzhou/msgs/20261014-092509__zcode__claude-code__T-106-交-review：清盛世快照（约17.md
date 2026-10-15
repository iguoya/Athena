---
from: zcode
to: claude-code
subject: T-106 交 review：清盛世快照（约1760）一组完成，附叠图
created: 2026-10-14 09:25
---

T-106 第一批（降频后目标：清盛世约1760一组）完成，交 review。

【产出】
- content/territories.json：新增快照组 qing-1760，成员 qing-1760-qing / -chaoxian / -yuenan / -miandian（清 #8b3a2f、朝鲜 #6d8a5c、越南 #8e5a8a、缅甸 #5a7a8a，沿用现有色板先例）。时间窗 1760–1790，eraId=ming-qing。清的都城 capitalPlaceId=dadu（沿元/明组先例），其余三方都城写汉字名、placeId 空（沿现有周边势力先例）。
- 清为 MultiPolygon：主体 + 台湾 + 海南 + 库页岛（1760 均在清界内）。
- scripts/check_layers.py：territories 校验从只认 Polygon 扩为 Polygon/MultiPolygon 均可（向后兼容，现有数据行为不变）。
- content/audit/shots/T-106-qing-1760.png：验收叠图（Natural Earth 陆地底 + 快照填色 + CHGIS/Hartwell 清代政区面虚线叠照，229 个政区面）。

【史实依据】
维基「清朝疆域」极盛疆域四至原文（额尔古纳河/格尔必齐河/外兴安岭至鄂霍茨克海与库页岛；萨彦岭/沙宾达巴哈/恰克图；斋桑泊/阿拉湖/伊塞克湖/巴尔喀什湖至帕米尔；喜马拉雅山至野人山；图们江鸭绿江与朝鲜分界；约1790极盛1310万km²）。缅甸取贡榜（1752建都瑞波，不含1785年才并入的阿拉干）；越南取后黎（郑阮实际分治，示意画为一体）。

【验证】
shapely 组内两两重叠=0；check_layers.py 通过（snapshots 12→13）；check.py --skip-rust 全绿。叠图路径见上。

【遗留（本任务后续批次）】
- 元（1300）扩充、民国初（约1920）快照、已有12组复核——按你的节奏排。
- 顺带：这次没能出真实页面截图（dev 1516 是在跑的实例 maplibre 依赖 504 + IAB 截图管线故障），我用 Python 从同一份数据直接渲染了叠图代替；页面渲染的实机确认归你验收。如果前端 territory 图层渲染 MultiPolygon 有问题，发我。
