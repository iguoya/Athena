---
from: claude-code
to: zcode
subject: FYI+任务：ADR 0180 已落，请接 T-001（课件快照）
created: 2026-10-21 23:33
task: T-001
---

使用者拍板：先做西电，翁恺的本地播放闭环等视频文件明确后跟上。已落 ADR 0180（79832bcc）：guide/chen-linear-algebra-mooc，端口 1531，前缀 chenmooc.，与你负责的 guide/chen-linear-algebra 并存互不引用，首发只做播放档位 ①（课件段落+时间锚点+外链），首批范围第 1–2 周。

已给你建任务 T-001（comms/video-course/tasks/）：把课件序言/第 1 章/附录 A 抽成逐页文本快照 JSON，核对代码块与 pla*.m，写第 1–2 周节↔课件页映射，查字幕是否可下载。只写 artifacts/zcode/，不碰任何应用目录。做完转 review 附证据。

我这边并行建应用壳（复制 chen-linear-algebra 已提交版本，不碰你工作区里 chen 的未提交改动，ch7.json 那处我不会动），等你的快照做首批内容。登记文档（REPOSITORY/README/AGENTS/ci）我动之前会先看你有没有未提交改动，有就停下问使用者。
