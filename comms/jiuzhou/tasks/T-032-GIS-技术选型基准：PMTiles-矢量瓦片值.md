---
id: T-032
title: GIS 技术选型基准：PMTiles 矢量瓦片值不值得迁
owner: cursor
status: todo
priority: P1
depends: 
created: 2026-10-14 14:28
updated: 2026-10-14 14:28
---
## 目标
使用者要求把先进 GIS 技术用进来（路线见 `docs/GIS-TEXT-FUSION.md` 线 C）。第一步**不盲目迁移**，先量、再决定：PMTiles 矢量瓦片（单文件，MapLibre 经 pmtiles 协议直接读）对我们是否值得。

## 做法
1. 基准：把学术层 19 切片 + `territories-clipped` + `landmarks` 转成 PMTiles（tippecanoe 不一定装得上，可用 Python 的 `pmtiles` + `mapbox-vector-tile` 或自写，选最省事的；转换脚本入库可重跑）。
2. 对比现状（懒加载 GeoJSON）：冷启动首绘、切年份渲染、内存、安装包体积。给出表格数字。
3. 写 `docs/decisions/` 下一篇应用 ADR（编号顺延）：采用/不采用、理由、迁移范围。**如果收益不明显就明说不迁**，不为新而新。
4. 若采用：只迁一个图层做样板（学术层），保持现有行为不变，可开关回退。

## 验收
- 基准表（含测量方法）、ADR、可重跑的转换脚本；`check.py --skip-rust` 绿。
- 如果新增依赖需要下载（pip/npm 包），写清楚包名、版本、体积，并在任务里记一笔——我会转给使用者确认后再装，不要自行大量下载。

## 进展记录
