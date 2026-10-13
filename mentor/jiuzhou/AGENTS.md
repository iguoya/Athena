# 九州 · Jiuzhou — 项目协作规则

仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **图谱/参考类**（仓库 ADR 0156）：中国历史地理图鉴，供历史爱好者自用查阅。不判分、
  不建进度库、不建 `content-contract.json`，跨应用教学规范不生效。
- 目录 `mentor/jiuzhou`，id `jiuzhou`，进程 `athena-jiuzhou`，端口 **1516**，
  启动器领域圈 **「兴趣」**，不挂靠。
- 界面名「九州」，英文副标 Jiuzhou（专名罗马化，非自造拼音缩写）。
- **时间主轴是政治秩序七段**（蒙元并入唐宋）；朝代只作标签。
- **空间自有历史**（本应用 ADR 0001）：年份滑块驱动全部带生命周期的图层；地点剖面与
  时间/主题入口并列。
- 内容版权由自用场景自负；出处鼓励在条目里注明并核对原文，不做门禁。
- **多代理并行：** 三方协作——`claude-code` 指挥/规划/验收，`cursor` 前端/地图，`zcode` 内容。
  通讯机制（收件箱 / 任务 / 消息 / 看板）见 [`docs/comms/README.md`](docs/comms/README.md)，
  分工与路径归属见 [`docs/PARALLEL.md`](docs/PARALLEL.md)。每轮开工先跑
  `python mentor/jiuzhou/scripts/comms.py inbox <你的名字>`；旧 `docs/HANDOFF-*.md` 已作废，仅作指路牌。

## 技术栈与选型理由

- 壳 **Tauri 2 + React 19 + TypeScript + Vite + Tailwind**（最初复制自
  `mentor/competitions`，此后独立演进；ADR 0062、0138）。
- **主图 MapLibre GL** + `@athena/maps`（仓库 ADR 0157、0158）：纸本底、岸线、河网、走廊；
  目标叠离线晕渲与 denser 公域河网（Natural Earth + 自绘）。
- **默认按真实年份 scrub**（可切事件序列）；阶段色带与事件密度柱（分期）；播放目标「年/秒」。
- **本机学术层**：CHGIS / 自备谭图系进 `.cache/maps/`，`prepare_local_maps.py`；有则叠、无则示意。
  勿提交 `.cache`。
- 动效用 Motion。Rust 端薄壳；读本机 `.cache` 需要时再加命令。

## 内容组织

```
content/
├── atlas.json        eras + places + events + people
├── territories.json  示意/多势力疆域快照（带 fromYear/toYear）
└── （路线等可进 atlas 或分文件，分期）
```

- **eras**：七段，id 稳定。
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
