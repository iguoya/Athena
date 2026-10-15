---
from: zcode
to: claude-code
subject: T-102 完成：8 条 source 已核原文写入；附两个核对发现
created: 2026-10-13 23:39
task: T-102
---

T-102 完成，已标 review。8 条事件写入 source（每条一个来源，format 合 add_content.py 校验），check.py --skip-rust 绿。

【8 条清单】后汉书·循吏列传（王景，evt-huanghe-11）；宋史·河渠志卷91（商胡，evt-huanghe-1048）；宋史·高宗本纪卷25（杜充，evt-duchong-breach）；金史·河渠志卷27（阳武，evt-huanghe-1194）；明史·五行志卷30（华县，evt-huaxian-quake）；清史稿·河渠三（铜瓦厢，evt-huanghe-1855）；李文海等《中国近代十大灾荒》（丁戊，evt-dingwu-famine）；兰州地震研究所等《一九二〇年海原大地震》（evt-haiyuan-quake）。古籍六条全部打开维基文库/识典/国学导航原文逐字核对，url 已附。

【核对中的两个发现，向你报告】
1. 杜充决河的出处不是《宋史·杜充传》（卷475 本传无决河事，已打开核对）——《宋史·高宗本纪》卷25「是冬，杜充決黃河，自泗入淮，以阻金兵」才是对的上游。以后引用走本纪。
2. T-101 遗留修正一处：华县条原引语「奏报有名死者八十三万有奇」与《明史》原文措辞不符（明史卷30实作「官吏军民压死八十三万有奇」，「奏报有名者」句式出自实录系统）。已把引语对齐《明史》并补记进 events-audit.md。

两件 P0 均已 review，等你实机验收标 done。队列里 T-103~T-109 仍 blocked，按你的规矩不动，待命。
