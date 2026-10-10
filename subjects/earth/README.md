# 地球（earth）

真实比例的地球分层 3D 可视化：大气五层（对流层 / 平流层 / 中间层 / 热层 / 外逸层）与
地球内部六层（地壳 / 上地幔 / 过渡带 / 下地幔 / 外核 / 内核），WGS 84 椭球 + PREM +
US Standard Atmosphere 1976 标准模型驱动。真实比例下薄层看不见是事实——四分之一剖面、
径向真实刻度尺、现象锚点（科拉钻孔到地球静止轨道）、径向探针与两张联动图表负责把
「薄」讲清楚。图谱/参考类，不判分（ADR 0128）。

```sh
python3 scripts/check.py                      # 数据标准值 + 构建 + 测试
../../launcher/target/release/launcher open earth
```
