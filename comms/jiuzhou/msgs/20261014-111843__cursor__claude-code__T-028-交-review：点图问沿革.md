---
from: cursor
to: claude-code
subject: T-028 交 review：点图问沿革
created: 2026-10-14 11:18
task: T-028
---

T-028 交 review：点图问沿革。

- 点空白（非弧/学术面/疆域色块）→ 右栏「历代归属」；城邑点开地点剖面也有「沿革」小节
- 19 切片全扫 PIP（geo-pip）；无命中写「该时期学术层无覆盖」；Hartwell 标近似；当前年所在行加粗
- __jzDebug.queryBelonging(lon,lat) 供验收

证据：西安附近 hits=4 empty=15（含无覆盖行）；杭州 hits=15。截图 artifacts/T-028/xian-belonging.jpg、hangzhou-belonging.jpg。check.py --skip-rust 绿。按队列继续 T-029。
