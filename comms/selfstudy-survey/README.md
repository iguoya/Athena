# selfstudy-survey 舱

「自考专业调查」（`mentor/selfstudy-survey`，ADR 0186）的采集与建设舱：调查 2025–2026 年全国各省计算机类（0809）、
电子信息类（0807）自考本科的开设格局、主考院校、课程计划、实践环节、教材大纲、报考毕业条件与变动。

## 角色与文件归属

| 成员 | 角色 | 名下路径 |
|---|---|---|
| claude-code | leader：ADR、数据模型、采集规程、应用代码与界面、验收（抽查原文） | `mentor/selfstudy-survey/`（除下行），`artifacts/claude-code/` |
| zcode | worker：按规程逐省采集，交证据与结构化数据 | `mentor/selfstudy-survey/content/provinces/`、`content/courses.json`、`content/textbooks.json`，`artifacts/zcode/` |

- 试点阶段（广东、江苏）leader 先自己写 `content/provinces/guangdong.json`、`jiangsu.json`，用来验证模型；zcode 同时独立采集同一批
  数据存到 `artifacts/zcode/`，两边**交叉核对**，差异即验收材料。试点验收后这两个文件移交 zcode 维护。
- 一个省一个文件（`content/provinces/<id>.json`），所以多个会话并行采集不同省份也不会撞车。
- cursor 暂不入舱（额度见 2026-10 的协作记录）；有额度后可作为第二个 worker，按省份分段。
- 任务号段：claude-code T-9xx，zcode T-0xx。

## 工作流

1. 开工：`python comms/comms.py triage zcode`（或 `inbox zcode --project selfstudy-survey`）。
2. 采集规程与数据模型见 [artifacts/claude-code/DESIGN.md](artifacts/claude-code/DESIGN.md)，**先读**。
3. 证据：原始页面文本快照、PDF 放 `artifacts/zcode/evidence/<省id>/`，每个文件头写 `url`、`fetched`（抓取日期）、`sha256`；
   应用目录里只放结构化结论加来源链接，不放整页文本。
4. 交付：写进你名下的 `content/provinces/<id>.json`，跑 `python mentor/selfstudy-survey/scripts/check.py --skip-rust`
   必须绿（脚本落地前先对照 DESIGN.md §3 自查），再转 `review`，`--note` 写覆盖了哪几个专业、几份计划、哪些格子是 pending 及原因。
5. **查不到就写 `pending`，不推断、不拿邻省凑**。第三方自考网（`report` 级）只能当线索，要再找到官方原文才能升级。
6. 验收：leader 抽查原文逐条核对（课程代码、学分、教材版次），抽查不过打回返工。

## 波次

| 波 | 内容 | 产出 |
|---|---|---|
| A | 31 省基线：考试院与自考官网入口、2025–2026 四个考期的时间、报考与学位政策 | 各省 `authority`、`calendar`、`policy` |
| B | 开设矩阵：核心专业 × 省份的开设状态、主考院校 | 各省 `offerings` |
| C | 课程计划：先试点五省，再铺开；课程行含学分、类别、实践要求 | 各省 `plans`、全局 `courses` |
| D | 教材与大纲：每门课的指定教材、版次、大纲出处 | `textbooks`、课程行引用 |

波次与分工在 T-001 的反馈后由 leader 定稿。
