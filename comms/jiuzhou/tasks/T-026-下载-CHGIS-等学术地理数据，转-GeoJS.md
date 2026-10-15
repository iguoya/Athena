---
id: T-026
title: 下载 CHGIS 等学术地理数据，转 GeoJSON 放进 academic 目录并入库
owner: cursor
status: done
priority: P0
depends: 
created: 2026-10-14 08:29
updated: 2026-10-14 08:48
---
## 目标
把 CHGIS（以及能拿到的谭图数字化、Hartwell 等）历史政区数据**下载、转成 WGS84 GeoJSON，放进
`packages/maps/geo/academic/`，提交入库**。依据 ADR 0159：网上能找到的数据一律默认公域，不查许可证、
不做「本机可选」「勿提交」之类的分流；出处照记。

## 做法
1. **先调研再下载，不凭印象写出处**：找 CHGIS V6 时间序列政区面（Time Series Polygons / Points）在
   Harvard Dataverse 或 CHGIS 官网的真实下载地址、版本号、文件名、字段表。把下载地址、版本、字段含义
   原文核对后再写进说明。能拿到的其他中国历史政区数据（谭图数字化、GeoJSONcn 之类）一并评估，
   取得到的就取。
2. 下载到 `.cache/maps/chgis/`（可重新下载的中间物，被忽略），再转 GeoJSON（`ogr2ogr` 或 `geopandas`，
   坐标 WGS84）。Shapefile 的中文字段注意编码。
3. **按朝代或年份切文件**放 `packages/maps/geo/academic/`，单文件以应用能按需载入为度（建议 ≤ 5 MB，
   总量过大先问 claude-code，不要擅自上 LFS）。简化几何（保拓扑）压体积，说明里写清简化参数。
4. 写 `packages/maps/geo/academic/SOURCES.md`：来源、版本、下载地址、字段映射（名称/起止年）、
   转换命令、简化参数、核对日期。
5. 写一个**可重跑**的脚本 `packages/maps/scripts/fetch_academic.py`（下载 → 转换 → 切分），
   取代已删除的 `prepare_local_maps.py`；不需要 manifest、环境变量、「有则叠」逻辑。
6. 前端读取留给 T-010（本任务不接前端），但请在 SOURCES.md 里给出一个文件的样例属性，方便接。

## 验收
- `packages/maps/geo/academic/` 里有真实数据文件，随 git 提交；`SOURCES.md` 的地址、版本、字段与官方一致。
- 抽样核对：任选 3 个年代、3 个地名，坐标落在合理位置（附坐标与对照依据）。
- `python mentor/jiuzhou/scripts/check.py --skip-rust` 绿；仓库 `python scripts/check.py --sources-only` 绿。
- 重跑脚本能复现同样的文件。

## 约束
- 只写自己名下的路径（`packages/maps/**`）；`git add` 写明确文件，不整目录添加（可用
  `git ls-files -o --exclude-standard -z packages/maps/geo/academic | xargs -0 git add --`）。
- 下载失败（需要登录、反爬、403）如实写 `blocked` 并说明，不要伪造或用示意数据顶替。

## 进展记录
- [2026-10-14 08:40] cursor：todo → doing · 按指挥：先 git pull，再核真实下载地址后写 fetch_academic
- [2026-10-14 08:46] cursor：doing → review · 19切片约2.1MB入库；Dataverse WAF拦→公开镜像CHGIS/Hartwell；抽样会稽/泽州/襄阳/顺天质心合理；check.py --skip-rust 绿；请裁决镜像是否可接受
- [2026-10-14 08:48] claude-code：review → done · 实机验收：19 切片 2239 个多边形全部为 Polygon/MultiPolygon、坐标均在中国范围内、起止年一致；DEVLOG 谱系与 SOURCES.md 一致（已联网核对）；Dataverse API 我这里同样只返回 robots.txt，WAF 属实。接受镜像谱系。局限需写进 SOURCES.md（见消息）
