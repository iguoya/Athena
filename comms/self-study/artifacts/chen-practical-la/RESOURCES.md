# 《实用大众线性代数（MATLAB版）》资源对照

给 zcode 建应用 / 拆任务用。cursor 于 2026-10-21 整理，未改应用目录。

## 书目

| 项 | 值 |
|---|---|
| 书名 | 实用大众线性代数（MATLAB版） |
| 作者 | 陈怀琛 |
| 出版社 | 西安电子科技大学出版社 |
| 出版 | 2014-08 |
| ISBN | 9787560634623 |
| 页数 | 约 156 |
| 定价 | 20 元 |

## 视频 / 慕课

- 中国大学 MOOC：https://www.icourse163.org/course/XDU-1001775006  
  （亦见 `XIDIAN-1001775006` 旧链；主讲陈怀琛、杨威）

## 作者主页（课件与程序集）

- 首页：https://see.xidian.edu.cn/faculty/hchchen/
- 下载列表：https://see.xidian.edu.cn/faculty/hchchen/html/download/
- 列表项（2014-11-10）：《实用大众线性代数(MATLAB版)》课件和程序下载  
  （具体 zip 直链需从该页点入；本机抓页若 404/空，以浏览器打开为准）

## 电子版线索（ADR 0159：自用入库）

- 采选系统书目页：https://www.aijiaocai.com/textbook/details?textbook_id=602289（有完整目录）
- 扫描 PDF 流传线索：文件名形态 `实用大众线性代数MATLAB版_13652907.pdf`（CSDN 等帖）
- 多蛋网条目（标称 30.78 MB 扫描 PDF）：https://www.duodown.com/material/340411796.html（下载需站内账号）
- 付费扫描站：千千图书 ebook/3301303（不优先）
- 京东读书有《工程线性代数（MATLAB版）》在线读，**不是**本书
- zcode 提及的藏书站线索：`101vv.com`（一零一藏书阁一类）
- **本机已试**：`pdf.windowsfront.com/jd_11558945.pdf` 仅 5 页/148KB 评论页拼装，**不是全书**（已放 `upstream/probe_windowsfront.pdf` 备查，勿当教材）
- **本机已试**：作者主页 `see.xidian.edu.cn` curl 被重定向，拿不到课件 zip 直链
- **待做**：浏览器登录多蛋网 / 101vv / 超星读秀拿完整 156 页扫描；或请使用者给出本机 PDF 路径（zcode 解读「找到电子版」也可能是用户已有）

## 与仓库现状的边界（建议，不作决定）

- 不混进 `self-study/linear-algebra`（自考 02198/13175）
- 不混进 `guide/selinger-linear-algebra` / `siefken-linear-algebra`（考研数二线代精读）
- 更像新的 `guide/<id>` 教材精读 + 本机 Octave 练习（zcode 会话里倾向 `chen-linear-algebra`、端口 1528、前缀 `chen.`、ADR 0177——待 grill 拍板）

## cursor 可立刻接手的机械块（待任务书）

1. 拿到 PDF / 程序集到 `comms/.../artifacts/` 或应用 `upstream/`（gitignore 规则按 zcode ADR）
2. 按章录入习题（题干、题号、页码、课堂/课后标记），出处 locator 齐全
3. MATLAB→Octave 兼容性抽查与答案复算（本机有 Octave 时）
