# 九州 · Jiuzhou

中国历史地理图鉴（图谱/参考类，仓库 ADR 0156；交互与内容模型见本应用
[ADR 0001](docs/decisions/0001-year-driven-spatial-history.md)）。

按**政治秩序七段**浏览；朝代只作标签。地图以**真实年份**驱动图层；目标是「空间自有历史」
（地点沿革、水利与路线生命周期、多势力疆域）。启动器领域圈「兴趣」，端口 **1516**。

```sh
launcher open jiuzhou
python3 scripts/check.py
```

内容真源：`content/atlas.json`。底图与示意水系在 `@athena/maps`；学术矢量仅本机
`.cache/maps/`（勿提交）。并行分工：[`docs/PARALLEL.md`](docs/PARALLEL.md)。
