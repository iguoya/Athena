# 九州 · Jiuzhou — 项目协作规则

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **宗旨（ADR 0004/0007，统领内容取舍）**：**主——还原并解释当时为什么那样**（按当时的生产力、社会结构与人们的认识，不用今天的框架和价值判断去套）；**次——在此基础上提供对今天有边界的参照**（可参照，不是指导、不是开药方，对不上就不写）。**不做精神寄托，不做炫耀，不做流水账。**收录：当时影响大，或今天有可对照的机制，满足其一；重要条目先立时代语境（ADR 0006），再说机制与得失；有参照时 `limits`（不可类比之处）必填。个人层同样讲处境与权衡、防幸存者偏差（ADR 0005）。
- **图谱/参考类**（仓库 ADR 0156）：中国历史地理图鉴，供历史爱好者自用查阅。不判分、
  不建进度库、不建 `content-contract.json`，跨应用教学规范不生效。
- 目录 `mentor/jiuzhou`，id `jiuzhou`，进程 `athena-jiuzhou`，端口 **1516**，
  启动器领域圈 **「兴趣」**，不挂靠。
- 界面名「九州」，英文副标 Jiuzhou（专名罗马化，非自造拼音缩写）。
- **时间主轴是政治秩序八段**（蒙元并入唐宋；第八段「当代」自 1949 讲到当下，数据带 `asOf`，ADR 0002）；朝代只作标签。**历史与现实不剥离**：地点有「今天」、事件有「今日回响」。
- **空间自有历史**（本应用 ADR 0001）：年份滑块驱动全部带生命周期的图层；地点剖面与
  时间/主题入口并列。
- 内容版权由自用场景自负；出处鼓励在条目里注明并核对原文，不做门禁。
- **多代理并行：** 三方协作——`claude-code` 指挥/规划/验收，`cursor` 前端/地图，`zcode` 内容。
  通讯走仓库公共服务 `comms/` 舱 `jiuzhou`（收件箱 / 任务 / 消息 / 看板），规则见
  [`../../comms/jiuzhou/README.md`](../../comms/jiuzhou/README.md)，分工与路径归属见
  [`docs/PARALLEL.md`](docs/PARALLEL.md)。每轮开工先跑
  `python comms/comms.py inbox <你的名字> --project jiuzhou`；旧 `docs/HANDOFF-*.md` 已作废，仅作指路牌。

## 技术栈与选型理由

- 壳 **Tauri 2 + React 19 + TypeScript + Vite + Tailwind**（最初复制自
  `mentor/competitions`，此后独立演进；ADR 0062、0138）。
- **主图 MapLibre GL** + `@athena/maps`（仓库 ADR 0157、0158）：纸本底、岸线、河网、走廊；
  目标叠离线晕渲与 denser 公域河网（Natural Earth + 自绘）。
- **默认按真实年份 scrub**（可切事件序列）；阶段色带与事件密度柱（分期）；播放目标「年/秒」。
- **学术层**：CHGIS / 谭图系等转成 GeoJSON 直接入库 `packages/maps/geo/academic/`（ADR 0159，
  取代 0158 的「本机可选」）；没有对应年层的时段用 `territories.json` 示意帧作底色。
- 动效用 Motion。Rust 端薄壳。

## 内容组织

```
content/
├── atlas.json        eras + places + events + people
├── territories.json  示意/多势力疆域快照（带 fromYear/toYear）
└── （路线等可进 atlas 或分文件，分期）
```

- **eras**：八段，id 稳定（`modern` 的 id 与范围不动，新增 `contemporary`）。
- **places**：坐标 + 古名区间 + `role`；目标加地位/隶属沿革（ADR 0001）。
- **events**：`year`、`eraId`、`placeId`（可扩 `placeIds`）、`lede`（≤40 字）、
  `summary`/`impact`（言简意赅，禁止灌水套话）、目标 `kind` / `geoWhy` / `source`；
  可选 `route`、`highlightPlaceIds`、`compare`。
- **people**：独立表；与 `personIds` 对齐。
- **禁止**用脚本为凑字数往 prose 追加复述句；存量先剥再写质量文。

## 建设顺序（ADR 0001）

- **P0** 年轴为主、剥灌水、文档七段、maps 河网/岸线加 dens、tier 中文。
- **P1** 地点剖面、多势力快照、都城迁移与人口重心。
- **P2** 路线动画、主题叙事、卷帘。
- **P3** 拉取管线、搜索、人物页、按质量扩事件。

## 开发与验证

```sh
launcher open jiuzhou
python3 scripts/check.py
python3 scripts/check.py --skip-rust
```

环境变量 `ATHENA_JIUZHOU_ROOT` 可强制指定应用根。影响本应用边界的决定写在
`docs/decisions/`；先 ADR 再动数据模型。
