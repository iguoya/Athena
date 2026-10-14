# `@athena/maps`

历史地理**纯呈现**包（ADR 0157、0158）。不写应用事件模型。

## 默认底图

- `paper-style`：MapLibre 纸本墨线底图（背景=海面 `#cfd8d4`）
- `geo/land.json`、`countries.json`：Natural Earth 50m 裁东亚并简化（≤250KB），由
  `scripts/build_base_layers.py` 生成；原始 zip 在 `.cache/maps/natural-earth/`
- `geo/coastline.json`、`hydro.json`、`corridors.json`：自研示意矢量  
  （`hydro.json` 已加密主干：黄河几字弯、长江中下游、淮河/珠江/海河/辽河/松花江/澜沧江/雅鲁藏布等）

## 学术层（直接入库，ADR 0159）

CHGIS / Hartwell 等转成 WGS84 GeoJSON 后放 `geo/academic/`，随仓库提交；
出处与字段见 `geo/academic/SOURCES.md`，切片索引见 `geo/academic/index.json`。

```sh
python packages/maps/scripts/fetch_academic.py
```

中间物在 `.cache/maps/chgis/`（可删）。官方 Dataverse 若被 WAF 拦住，脚本会改走已记录的公开镜像并在 SOURCES 写明。

### 疆域贴海岸（T-017）

```sh
python packages/maps/scripts/clip_territories.py
```

用 `geo/land.json` 裁剪 `mentor/jiuzhou/content/territories.json`，写出
`geo/territories-clipped.json`（不回写 content）。九州前端读裁剪结果。

### 黄河与长江主干（Natural Earth 10m，已入库）

`geo/hydro.json` 里的 `huanghe`、`changjiang` 由 NE 河流中心线重建（最短路径取主干、
简化到约 1 km），与已知地点偏差 ≤10 km。其余河仍是手绘示意线。

```sh
# 1. 下载 CC0 包到 .cache/maps/natural-earth/
#    https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.zip
# 2. pip install pyshp shapely
python packages/maps/scripts/densify_hydro.py            # 只写 geo/hydro.json
python packages/maps/scripts/densify_hydro.py --jiuzhou  # 另改写九州的 hydro.json / features.json
```

## 晕渲（hillshade）

东亚灰度晕渲已落地（九州 T-007）：Natural Earth `GRAY_50M_SR_OB` 裁到 lon 70–145 /
lat 15–55，写成 `geo/relief-east-asia.webp`（≤3MB，入库）。原 zip 在
`.cache/maps/natural-earth/`，不提交。

```sh
python packages/maps/scripts/prepare_relief.py
```

应用侧用 MapLibre `image` + `raster`（opacity ≈0.35）叠在陆面色块上。更高精度 DEM
瓦片另议。

## 坐标与投影的两条铁律
1. **一律 WGS84 经纬度。** 若坐标来自国内地图服务（高德、腾讯为 GCJ-02，百度为 BD-09，带故意偏移，约 0.3–0.7 km 至更大），入库前必须先换算回 WGS84；公开学术数据（CHGIS、CBDB、Natural Earth）本身是 WGS84，无需处理。2026-10-14 用 CBDB 地址表核对了我们的 165 个地点：中位偏差约 2 km，无系统性偏移。
2. **栅格必须先按 Web 墨卡托行重采样，再交给 MapLibre 的 `image` source。** Natural Earth 栅格是 Plate Carrée（行与纬度线性），MapLibre 只收四个角点并在墨卡托空间里线性拉伸，两者不一致会让栅格整体偏移——35°N 附近约 2.6°（≈290 km），表现为「地图本身没问题、城市相对位置也没问题，叠在一起却整体错位」。`prepare_relief.py` 已处理，`check.py` 会校验 `relief-east-asia.json` 的 `projection`。
