---
id: T-003
title: 附录 G 缺译段补译（gmmproc）
owner: cursor
status: review
priority: P2
depends: T-002
created: 2026-10-18 19:49
updated: 2026-10-18 21:03
---
## 目标
补译附录 G「Wrapping C Libraries with gmmproc」（`chapter-wrapping-c-libraries`，7 页）的缺译段：共 47 段（约 1570 词）`zh` 为空，其余章已译完。**只译 `zh` 为空的 para/listitem**，`heading`/`figure`/`code` 块不译，已有译文不动。

## 做法
- 直接写草稿，**不改 `guide/gtkmm/`**：在 `artifacts/cursor/appendix-g.json` 里按 `{"<节 id>": {"<块序号>": "中文译文"}}` 的格式给出（块序号 = 快照 `content/chapters/chapter-wrapping-c-libraries/<节>.json` 里 `blocks` 数组的下标，从 0 起）。leader 用脚本合并进快照。
- 英文原文看上述快照的 `text`；行内代码保持反引号原样，Markdown 链接 `[文字](url)` 的 url 原样保留、文字可译。
- 术语严格按 `guide/gtkmm/content/glossary.json`（widget=部件 等；写完前自己对照一遍）；gmmproc、`_WRAP_METHOD` 等宏名、API 名、文件名一律保留原文。
- 译文忠实、简洁，不扩写、不加原文没有的断言；拿不准的句子在 `T-003-delivery.md` 里列出，不要蒙。

## 验收
47 段全部有译文且块序号对得上；术语无禁用写法；delivery 列出不确定处。完成后 `status T-003 review --note "段数/不确定处数"`。

## 进展记录
- [2026-10-18 20:50] cursor：todo → doing
- [2026-10-18 21:03] cursor：doing → review · 47 段；不确定 2 处。自检 empty=47 draft=47 missing/extra/glossary 均为 0。证据 comms/gtkmm-demo/artifacts/cursor/appendix-g.json 与 T-003-delivery.md
