# 北京（beijing）证据索引

采集：zcode（前会话 2026-10-24 抓主体并试 FineReport，本会话 2026-11-02 补时间表并入库）。

| 文件 | 来源 URL | 覆盖字段 |
|---|---|---|
| bj-2026arr.html | https://www.bjeea.cn/html/selfstudy/xxfbt/2025/1125/87664.html | offerings（44 专业总表：080901 open、080903 stopped、48 none）、events[2025-11-25]、matched_by（01B 自有码同名映射） |
| bj-2026-04-sched.pdf | https://www.bjeea.cn/uploads/soft/251125/北京市高等教育自学考试2026年4月笔试课程考试时间表.pdf | calendar[2026-04]（4/11-12）；01B0015/01B0017 同组课程清单 |
| bj-2026-10-sched.pdf | https://www.bjeea.cn/uploads/soft/251125/北京市高等教育自学考试2026年10月笔试课程考试时间表.pdf | calendar[2026-10]（10/24-25） |
| bj-2026-textbook.pdf（.txt 转写） | 同 87664 通知附件 4 | 2026 全年教材信息表（课程×教材×类型），complete.textbook 依据 |
| bj-zkxcx.html / bj-zyjh.html / bj-zyjh-api2.html | http://zkxcx.bjeea.cn/（FineReport 报表） | 专业计划查询系统探测记录（会话化接口未突破，01B0015 学分/类别明细未获得——NEEDS-HUMAN） |

bj-zhinan/bj-zikao/bj-aizikao/bj-home 等栏目快照在前会话 .work 留档，policy 四项暂 null 待下批补。
