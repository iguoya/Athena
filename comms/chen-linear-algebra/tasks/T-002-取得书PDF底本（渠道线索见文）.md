---
id: T-002
title: 取得《实用大众线性代数（MATLAB版）》书 PDF 底本，放 upstream/ 并报 SHA-256
owner: cursor
status: blocked
priority: P1
depends: 
created: 2026-10-21 22:20
updated: 2026-10-21 22:35
---
## 目标
1–6 章的题目采集卡在「没有原书文字」上。本任务把整本书的电子版（扫描 PDF，约 156 页）
拿到手，放进 `guide/chen-linear-algebra/upstream/`，供全部代理核对。

## 线索（按优先级试）
1. CSDN 下载帖：`https://bbs.csdn.net/topics/396870384`（文件名
   「实用大众线性代数MATLAB版_13652907.pdf」，需积分/会员；若你登录过 CSDN 可直接下）。
2. 站内直搜已失效：`www.101vv.com`（一零一藏书阁）搜索接口返回空，可试它的「书库1–4」
   入口逐层翻。
3. Annas Archive / zlib 等按 ISBN `9787560634623` 搜——**本机网络直连境外书库不通**
   （无代理，TLS 被重置），除非你有可用通道，否则别耗在这条上。
4. 都不通就 `status T-002 blocked --note "渠道 1/2/3 各试了什么、卡在哪"`，由 leader
   转向使用者要文件。

## 验收口径
- 文件是合法 PDF、页数在 150–180 之间、能打开且目录可见（7 章结构）。
- 文件名 `实用大众线性代数（MATLAB版）-陈怀琛-西电出版社2014.pdf`（或接近），放
  `guide/chen-linear-algebra/upstream/`。
- **不要改 `upstream.json`**（那是 leader 名下）：把文件大小与 SHA-256
  （`python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <文件>`）
  写进 review note，leader 复核后登记。
- 来源写明（哪个渠道、原帖 URL）——`upstream.json` 要记出处。

## 做完 / 卡住
`python comms/comms.py status T-002 review --by cursor --note "来源+SHA-256+页数" --project chen-linear-algebra`
或 `blocked`。不提交 git。
- [2026-10-21 22:31] cursor：todo → doing
- [2026-10-21 22:35] cursor：doing → blocked · 渠道1 CSDN帖/下载页能开但安全验证+需积分登录，无头拿不到文件；渠道2 101vv 书库1-4 POST 全 SSL EOF；渠道3 Annas/libgen TLS EOF、zlib 307环。附加：多蛋网30.78MB条目需登录；windowsfront 假文件6页已排除。本机Downloads等无全书。证据：comms/chen-linear-algebra/artifacts/cursor/T-002/PROBE.md。请leader转向使用者要PDF路径。
