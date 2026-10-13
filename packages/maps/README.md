# `@athena/maps`

历史地理**纯呈现**包（ADR 0157、0158）。不写应用事件模型。

## 默认（可再分发）

- `paper-style`：MapLibre 纸本墨线底图（背景=海面 `#cfd8d4`）
- `geo/land.json`、`countries.json`：Natural Earth 50m 裁东亚并简化（≤250KB），由
  `scripts/build_base_layers.py` 生成；原始 zip 在 `.cache/maps/natural-earth/`
- `geo/coastline.json`、`hydro.json`、`corridors.json`：自研示意矢量  
  （`hydro.json` 已加密主干：黄河几字弯、长江中下游、淮河/珠江/海河/辽河/松花江/澜沧江/雅鲁藏布等）

## 本机学术层（自用，不进 git）

把 CHGIS / Hartwell / 自备谭图数字化包放到仓库根或应用下的 `.cache/maps/`，或设
`ATHENA_MAPS_DATA` 指向目录。运行：

```sh
python packages/maps/scripts/prepare_local_maps.py
```

会生成 `.cache/maps/manifest.json` 与可选年层 GeoJSON；九州有则叠、无则降级示意层。
**勿**把 `.cache` 提交进版本库。

### Natural Earth 河网再加密（可选）

```sh
# 1. 下载 CC0 包到 .cache/maps/natural-earth/
#    https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip
# 2. pip install pyshp
python packages/maps/scripts/densify_hydro.py
```

写出 `.cache/maps/hydro-dense.json`（裁切中国框、匹配九条主干）。体积大，**不入库**；
默认包仍用仓库内示意 `geo/hydro.json`。

## 晕渲（hillshade）

东亚灰度晕渲已落地（九州 T-007）：Natural Earth `GRAY_50M_SR_OB` 裁到 lon 70–145 /
lat 15–55，写成 `geo/relief-east-asia.webp`（≤3MB，入库）。原 zip 在
`.cache/maps/natural-earth/`，不提交。

```sh
python packages/maps/scripts/prepare_relief.py
```

应用侧用 MapLibre `image` + `raster`（opacity ≈0.35）叠在陆面色块上。更高精度 DEM
瓦片仍可走本机 `.cache`（`prepare_local_maps.py`），不进发行包。
