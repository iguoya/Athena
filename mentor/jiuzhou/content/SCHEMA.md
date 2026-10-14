# 内容 schema 增补说明（供 cursor 做界面）

由 zcode 维护；T-112/T-113/T-118 新增字段在此登记。**所有新字段一律可选，前端读不到时静默降级。**

## atlas.json 顶层

- `asOf: 2025` — 当代篇数据的截止年份（T-113）。前端可显示「数据截至 2025」。

## eras[]

- `base`（T-118 时代底座，ADR 0006）：`{ productive, social, mind, basis[] }`。
  - `productive` 生产力（技术/农业/交通/人口资源条件）；`social` 社会结构（阶层/土地赋役/政治结构）；`mind` 当时人的认识（主流观念/信息条件/认知局限）。每项 2–4 句，只写条件不写评价。
  - `basis[]`: `{ work, loc, url? }` 署名出处，同事件的 `source` 格式。
  - 已写：warring-unify、tang-song-plural、modern；其余 5 个时代待补。

## events[]（可选字段）

- `context`（T-118，ADR 0006 时代语境）：`{ productive?, social?, mind? }`，只写与该事件相关的项；`mind` 尽量写「当时人怎么看、他们不知道什么」。
- `source: [{ work, loc, url? }]`（T-102 起）：出处，官方文献/正史原文优先。
- `recent: true`（T-113）：近十年内的当代篇条目。
- 待定字段（T-114/T-115）：地点 `today`、事件 `today`/`lesson`/`legacy`、主题叙事 `lessons{problem,gains,losses,mechanism,applicability,limits,today,basis}`——落地时在此登记。

## 依据与纪律

- 出处底线（仓库 ADR 0043）：不凭印象伪造出处；条目里引用的句子的原文页 URL 见 `content/refs/`。
- 措辞纪律（ADR 0007）：见 `docs/ANACHRONISM-GUIDE.md`。
