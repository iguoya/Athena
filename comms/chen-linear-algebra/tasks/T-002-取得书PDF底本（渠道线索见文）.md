---
id: T-002
title: 取得《实用大众线性代数（MATLAB版）》书 PDF 底本，放 upstream/ 并报 SHA-256
owner: cursor
status: blocked
priority: P1
depends: 
created: 2026-10-21 22:20
updated: 2026-10-22 23:06
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
- [2026-10-22 22:14] zcode：blocked → blocked · cursor 无额度，zcode 接手跟进。三条主渠道 + 附加源的试探记录已入库（本任务文件与 artifacts/cursor/T-002/），接手后同样拿不到：这不是代理能力问题，缺的是合法来源——需要使用者提供本机已有的书 PDF 路径，或已登录可下的渠道。在那之前维持 blocked。
- [2026-10-22 22:19] zcode：blocked → blocked · 解除条件更新：使用者有实体书，可按需拍照——照片放 guide/chen-linear-algebra/upstream/book/（命名与处理约定见该目录 README）。底本不必再等整本 PDF：哪页需要拍哪页，照片落到即可解锁对应的转录、核对与页码对照工作。图表页（doc 里 [pic] 占位的曲线图、程序输出）优先。
- [2026-10-22 23:06] zcode：blocked → blocked · 使用者决定遗留：等其准备好再处理，期间不催、不再试渠道（本条由 claude-code 受使用者之托代记）。拍照接口已就绪（guide/chen-linear-algebra/upstream/book/README.md，命名 p<书页码>-<内容标识>.jpg）；使用者放入照片后按需解锁转录与 1–6 章题目采集。
