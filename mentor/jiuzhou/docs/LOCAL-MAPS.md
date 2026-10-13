# 本机学术地理包放置说明

九州默认只用 `@athena/maps` 的公域/自研示意层，**不依赖**任何学术数据即可完整浏览（ADR 0158）。
学术层（CHGIS / Hartwell / 自备谭图系数字化包）是本机自用的加成：有则叠，无则静默降级。

## 纪律

- 数据**只放本机**，目录是仓库根 `.cache/maps/`（已被 `.gitignore`），**绝不 `git add`**。
- 不把原始数据或其衍生 GeoJSON/SHP 复制进 `content/` 或 `packages/`；那两处会进版本库。
- 版权自负，仅供自用，不分发（与 ADR 0156 一致）。

## 放哪里

```text
<repo>/.cache/maps/
├── academic/   自备的谭图系 / GeoJSONcn 年层（*.geojson）
├── chgis/      CHGIS 或 Hartwell 解压、转换后的 GeoJSON
└── manifest.json   由脚本生成，勿手改
```

数据在别处时，设环境变量 `ATHENA_MAPS_DATA` 指向一个内部结构相同的目录。

## 怎么接入

```sh
python packages/maps/scripts/prepare_local_maps.py
```

脚本会扫描上述目录里的 `*.geojson`（以及 `type=FeatureCollection` 的 `*.json`），生成
`.cache/maps/manifest.json`。九州启动时读清单，**有则叠加，无则降级**。脚本不会下载任何东西。

## 数据准备时要注意

- 官方发布包常是 Shapefile，需先用 `ogr2ogr` 或 `geopandas` 转成 GeoJSON（WGS84 经纬度）。
- 政区面要带名称和起止年份属性，应用才能按年份显示；具体字段名**以你下载的包实际内容为准**，
  接入时的读取约定由 `packages/maps` 维护，本文不重复。
- 面数很多的包先按朝代或年份切成若干文件，避免一次载入过大。

## 与示意层的关系

- `content/territories.json` 里的疆域是**示意**，标注为 `schematic` 或 `snapshot`，
  不是考据；有学术层时以学术层为准，示意层退为底色。
- 示意层的边界是我们自己画的粗框，不要把它截图当疆域依据。
