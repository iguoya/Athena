# 学术层来源（packages/maps/geo/academic）

核对日期：2026-10-14

## 官方入口（原文）

- CHGIS V6 说明：https://chgis.fas.harvard.edu/data/chgis/v6/
- Dataverse 集合：https://dataverse.harvard.edu/dataverse/chgis_v6
- 时序府级面：`v6_time_pref_pgn_utf_wgs84.zip`，doi:10.7910/DVN/I0Q7SM
- Hartwell GIS v5：doi:10.7910/DVN/29302

## 本批实际下载路径

Harvard Dataverse 在本机自动化访问时被 AWS WAF 拦截（API 返回 `robots.txt` 正文，浏览器页同样空白）。
探测结果：`ok=False` · `reason=aws-waf-robots-txt`。

因此本批从公开镜像拉取已转好的朝代切片：
- 仓库：https://github.com/pessimistcamellia/china-history-map
- 路径：`v2/data/geo/<slice>.json`
- 镜像方说明（DEVLOG）：https://raw.githubusercontent.com/pessimistcamellia/china-history-map/main/DEVLOG.md

镜像方声明的谱系（摘录）：
- 秦汉等早期：CHGIS V6 `v6_time_pref_pgn_utf_wgs84`（WGS84）
- 唐宋元明等：Hartwell GIS v5（已由镜像方转 WGS84）
- 几何曾做过 Douglas-Peucker 简化（非官方原精度）

## 字段映射（要素属性）

| 入库字段 | 含义 | 来自镜像 |
|---|---|---|
| `name` | 政区中文名 | `name` |
| `name_py` | 拼音 | `name_py` |
| `type_ch` | 政区类型（郡/州/府…） | `type_ch` |
| `beg_yr` / `fromYear` | 存续起年（CE，负数为前） | `beg_yr`；缺则用切片年 |
| `end_yr` / `toYear` | 存续止年 | `end_yr`；缺则用切片年 |
| `source` | `chgis-v6` 或 `hartwell-v5` | 本脚本写入 |
| `sliceId` / `sliceTitle` | 所属切片 | 本脚本写入 |
| `sys_id` | CHGIS 原始 ID（若有） | `sys_id`/`SYS_ID`；镜像多数未带 |

切片级 `fromYear`/`toYear` 见同目录 `index.json`（给 T-010 / T-110 按年对表）。

## 样例属性（秦·会稽郡）

```json
{
  "name": "会稽郡",
  "name_py": "Kuaiji Jun",
  "type_ch": "郡",
  "beg_yr": -222,
  "end_yr": -211,
  "fromYear": -222,
  "toYear": -211,
  "source": "chgis-v6",
  "sliceId": "qin",
  "sliceTitle": "秦"
}
```

## 抽样核对（质心，手工）

| 切片 | 地名 | 存续 | 质心 (lon,lat) | 对照 |
|---|---|---|---|---|
| `qin` | 会稽郡 | -222–-211 | 119.86, 30.02 | 浙东合理 |
| `tang` | 泽州 | 627–741 | 112.77, 35.60 | 晋东南合理 |
| `ming` | 襄阳府 | 1476–1911 | 111.87, 32.07 | 鄂北合理 |
| `qing` | 顺天府 | 1743–1911 | 116.83, 39.67 | 京津合理 |

## 已知局限（出自镜像 DEVLOG，入库时照录）

1. **Hartwell（唐宋元明等 `hartwell-v5` 切片）**是用现代县域边界「拼接」历史政区的近似值；前端图例（T-020）应对此类标「近似」。
2. **秦**仅约 13 郡，且集中在东南；关中/西部无面。
3. **唐**关中/长安一带常无多边形覆盖（CHGIS 早期面偏东）；勿把空白当成「无政权」。
4. **几何**经 Douglas-Peucker 简化（ε 约 0.03°–0.5°），非官方原精度。
5. 本批未直接从 Harvard Dataverse 拉官方 zip（本环境 AWS WAF）；谱系以镜像 DEVLOG + 字段形态核对。

## 重跑

```sh
python packages/maps/scripts/fetch_academic.py
```

中间文件在 `.cache/maps/chgis/mirror/`（可删，可重下）。产出扩展名为 `.json`（便于 Vite 打包）。

## 切片清单

| id | 文件 | 标题 | from | to | 谱系 | 要素数 | 字节 |
|---|---|---|---|---|---|---|---|
| qin | `qin.json` | 秦 | -221 | -206 | chgis-v6 | 13 | 39668 |
| han-west | `han-west.json` | 西汉 | -206 | 9 | chgis-v6 | 18 | 37365 |
| han-east | `han-east.json` | 东汉 | 25 | 220 | chgis-v6 | 16 | 36556 |
| three-kingdoms | `three-kingdoms.json` | 三国 | 220 | 280 | chgis-v6 | 25 | 43008 |
| jin-west | `jin-west.json` | 西晋 | 265 | 316 | chgis-v6 | 38 | 54173 |
| southern-northern | `southern-northern.json` | 南北朝 | 420 | 589 | chgis-v6 | 69 | 69129 |
| sui | `sui.json` | 隋 | 581 | 618 | chgis-v6 | 78 | 79270 |
| five-dynasties | `five-dynasties.json` | 五代 | 907 | 960 | chgis-v6 | 130 | 116880 |
| tang | `tang.json` | 唐 | 618 | 907 | hartwell-v5 | 115 | 105692 |
| song-liao | `song-liao.json` | 北宋/辽 | 960 | 1127 | hartwell-v5 | 164 | 135035 |
| liao | `liao.json` | 辽 | 907 | 1125 | hartwell-v5 | 106 | 96341 |
| song-jin | `song-jin.json` | 南宋/金 | 1127 | 1279 | hartwell-v5 | 165 | 137425 |
| jin | `jin.json` | 金 | 1115 | 1234 | hartwell-v5 | 190 | 135210 |
| xixia | `xixia.json` | 西夏 | 1038 | 1227 | hartwell-v5 | 1 | 3868 |
| xixia-1200 | `xixia-1200.json` | 西夏（1200 切片） | 1200 | 1200 | hartwell-v5 | 6 | 14755 |
| yuan | `yuan.json` | 元 | 1271 | 1368 | hartwell-v5 | 231 | 216638 |
| ming | `ming.json` | 明 | 1368 | 1644 | hartwell-v5 | 246 | 234048 |
| qing | `qing.json` | 清 | 1644 | 1911 | chgis-v6 | 281 | 277667 |
| republic | `republic.json` | 民国 | 1912 | 1949 | chgis-v6 | 347 | 343721 |

