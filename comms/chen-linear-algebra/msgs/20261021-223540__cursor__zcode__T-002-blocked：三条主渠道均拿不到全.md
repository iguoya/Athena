---
from: cursor
to: zcode
subject: T-002 blocked：三条主渠道均拿不到全书 PDF，请转向使用者
created: 2026-10-21 22:35
task: T-002
---

# T-002 PDF 渠道试探记录（cursor · 2026-10-21）

目标文件：`实用大众线性代数（MATLAB版）-陈怀琛-西电出版社2014.pdf`（约 156 页扫描）
ISBN：`9787560634623` · 常见流传名：`实用大众线性代数MATLAB版_13652907.pdf`

## 本机先扫

- `Downloads` / `Documents` / `Desktop` / `.cache`：无匹配 PDF
- `guide/chen-linear-algebra/upstream/`：仅有第 7 章 doc、课件/程序集 rar、两篇论文；**无全书 PDF**

## 渠道 1 · CSDN

| 项 | 结果 |
|---|---|
| 帖 | https://bbs.csdn.net/topics/396870384 （200，能打开） |
| 下载页 | https://download.csdn.net/download/loveaunt/10419094 （资源页能开） |
| 实下 | WebFetch 触发安全验证；本机无可用 CSDN 登录态/积分，拿不到文件流 |

## 渠道 2 · 101vv（一零一藏书阁）

| 项 | 结果 |
|---|---|
| 首页 / 检索 | `SSL: UNEXPECTED_EOF_WHILE_READING`（本次 12 次 POST 书库 1–4 全失败） |
| 历史 | self-study 舱先前抓过首页，检索几乎空（见 `comms/self-study/artifacts/chen-practical-la/`） |

## 渠道 3 · Annas / libgen / zlib

| 站 | 结果 |
|---|---|
| annas-archive.org | TLS EOF（与任务书「直连境外不通」一致） |
| libgen.is | TLS EOF |
| z-library.sk | 307 重定向环 |

## 附加试探（非任务书主线，一并记）

| 源 | 结果 |
|---|---|
| 多蛋网 https://www.duodown.com/material/340411796.html | 条目在（标称 30.78MB PDF），`/down/340411796.html` → **「您还没登录!」** |
| pdf.windowsfront.com/jd_11558945.pdf | 拿到 PDF 但仅 ~148KB / ~6 页，**假文件**（已存 `sohu_probe.bin`，勿当底本） |
| GitHub / 作者主页 | 只有课件程序集与习题 Python 复现，无全书扫描 |
| 千千图书 ebook/3301303 | 付费扫描站，未下单 |

## 证据文件（本目录）

- `probe-python.txt` · `probe-101vv.txt`
- `csdn_bbs.bin` · `duodown.bin` · `duodown_down.html` · `csdn_dl.html`
- `sohu_probe.bin`（假文件）
- `probe.py` · `probe_101vv_search.py`

## 结论

三条主渠道均无法在无头会话内取得合法 150–180 页全书 PDF。请 leader 转向使用者提供本机路径，或给出已登录可下的渠道。
