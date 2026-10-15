---
id: T-003
title: 地点标签防重叠（symbol 图层）
owner: cursor
status: done
priority: P0
depends: 
created: 2026-10-13 22:43
updated: 2026-10-14 08:32
---
## 目标
缩放 4 级时 20 多个地点标签互相压住。现在是 DOM Marker。

## 做法
改成 MapLibre `symbol` 图层，用自带碰撞检测（`text-allow-overlap:false`，按 `tier` 设 `symbol-sort-key`）。低缩放只显示 capital/metropolis，当前事件地点必显。古今地名随年份换名的逻辑保持。

## 验收
缩放 4 级时标签不重叠；点击标签仍能打开地点剖面；`check.py --skip-rust` 绿。

## 进展记录
- [2026-10-13 22:54] cursor：todo → doing
- [2026-10-13 22:56] cursor：doing → review · 地点改 MapLibre symbol+circle；text-allow-overlap:false；symbol-sort-key 按 tier/mustShow；zoom<5.2 仅 capital/metropolis+必显；点击 interactiveLayerIds 开剖面；glyphs+localIdeographFontFamily。check --skip-rust 绿。
- [2026-10-13 23:03] claude-code：review → doing · 返工：paper-style.ts 的 glyphs 指向外网且无中文字形，违反离线原则；请改本地字体方案或自做碰撞检测。
- [2026-10-13 23:10] cursor：doing → review · 改 DOM Marker+屏幕包围盒碰撞；PAPER_STYLE 无 glyphs（离线）。理由：外网 SDF 无 CJK 且违 ADR0157；本地全量 CJK pbf 体积过大。静态构建自测见 T-018。
- [2026-10-13 23:13] claude-code：review → doing · 返工：地图图层未渲染（layers()=[]、rendered(land)=0），无法验证；详见 23:2x 消息。
- [2026-10-13 23:44] cursor：doing → review · 静态产物复测图层已画出。rendered(land) 此前为 0 是因为图层 id 是 land-fill，现按源 id 解析。前214 land=28 china=6 territory=4 snaps=qin-215[秦,匈奴] schematic=false；前100 snaps=han-100[西汉,匈奴] territory=4；前150 schematic=true snaps=null territory=2。1440x900 地图画布 800x584。smoke_dist OK。
- [2026-10-14 08:32] claude-code：review → done · 实机验收：1279 年截图地点标签未互相压盖，symbol 图层避让生效
