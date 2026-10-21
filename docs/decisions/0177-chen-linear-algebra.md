# ADR 0177：新增 `guide/chen-linear-algebra`——陈怀琛《实用大众线性代数（MATLAB 版）》精读，Octave 实践做题

- 日期：2026-10-21
- 状态：已接受（使用者指派：「针对这本书编写一个教学应用来学习这本书，我打算本地使用
  Octave 实现书中的习题练习；这个应用最好支持做题，不管是课堂习题还是课后作业习题，
  出题必须有所本，不要凭空制造」；id 与目录名经使用者确认选 `chen-linear-algebra`）
- 关系：应用形态沿用 [ADR 0143](0143-guide-manual-apps.md)（`guide/` 装跟随一本外部手册/
  教材精读的应用）与 [ADR 0163](0163-math-tool-tutorials-in-guide.md)（一本书或一门课一个
  `guide/` 应用、示例用真工具复跑）；同圈同类先例 [ADR 0162](0162-linear-algebra-readers-in-guide.md)
  （两本线代教材精读）；出处分档按 [ADR 0043、0089](0089-source-tiers.md)；公域入库按
  [ADR 0159](0159-public-domain-by-default.md)；方法原型按 [ADR 0113](0113-dominant-learning-methods.md)；
  宁缺毋滥按 [ADR 0129](0129-quality-over-quantity.md)；内容三层不走按 [ADR 0028](0028-three-layers.md)

## 背景

陈怀琛（西安电子科技大学教授）是国内「用 MATLAB 改造线性代数教学」的代表学者。《实用大众
线性代数（MATLAB 版）》，西安电子科技大学出版社 2014 年 8 月，ISBN 978-7-5606-3462-3，
约 156 页，是他这一路线的大众读本：用消元法解方程组（适定、超定、欠定）、用向量空间理解
线性代数、线性变换的实际应用，全程带着 MATLAB 算例走。该书有西电官方配套慕课「实用大众
线性代数（MATLAB 版）」（中国大学 MOOC，陈怀琛、杨威主讲）作为视频版。

使用者已取得该书电子版，打算以 Octave（本机已装的 MATLAB 等价工具）实现书中习题，要求
应用支持做题且出题必须有所本。`guide/` 圈已有两种成熟形态：selinger/siefken 是英文开源
教材的「原文快照 + 译文」精读；octave-manual 是英文手册精读配自编「试一试」，答案必须由
本机 Octave 复算入库。本书是中文正式出版物：没有翻译管线，重心天然落在**题目与 Octave
实践**上。

## 决策

1. **新增 `guide/chen-linear-algebra`**，`group` 为「数学」。id 与目录名
   `chen-linear-algebra`（作者姓氏，同 `selinger-`/`siefken-` 的「作者-课程」惯例）；
   进程 `athena-chen-linear-algebra`；知识点前缀 `chen.`；dev 端口 1528；进度库
   `AthenaChenLinearAlgebra/learning.db`，`attempts` 表 append（ADR 0037、0155）。
2. **学习应用，出处档位 `open`，但题源是应用级硬门禁**（使用者要求「出题必须有所本，
   不要凭空制造」）：每道入库题目必须带 `source_refs`——`relation: verbatim`（原书习题、
   例题原样录入）或 `adapted`（以原书题为底改数字/改问法，注明改动点），`locator` 给
   页码与题号/例题号。**自编题（`authored`）默认不入题库**，要入须在 `note` 写明原书
   覆盖不到的理由并经使用者认可。应用 `scripts/check.py` 强制执行：判分条目缺出处或
   locator 缺页码/题号即报错，不阻断不收口。跨应用出处检查不扫 `guide/`，这层门禁
   归应用自己的检查（同 selinger 的先例）。
3. **方法原型**（ADR 0113）：主**预测–运行**（先预测输出，再在 Octave 里运行对照——
   原书的教学法本来就是「用工具算着学」），辅**真做校验**（答案由本机 Octave 复算，
   `verify` 字段写复算代码，`check.py` 在装有 Octave 时复跑）。
4. **内容形态**：章节结构与编号跟随原书目录（以电子版实物核对后定，不用二手资料）。
   每章 = 章导学（自编，讲这一章在学什么、Octave 里用哪些函数，引用原书处标注出处）+
   原书例题与习题入库成题库。原书代码是 MATLAB：练习一律以 Octave 等价写法呈现（线代
   核心语法兼容），确有差异处（图形、个别函数）在题面加注，不冒充原书原文。
5. **底本与视频**：电子版 PDF 放 `upstream/` 入库（ADR 0159：网上能找到的数据默认公域，
   出处照记——出版社、年份、ISBN）；它是全部 `verbatim` 出处的最终核对物。慕课视频
   **不下载入库**，以链接登记在 `upstream.json` 与 README，学习者在线看。
6. **技术栈与壳**：Tauri 2 + React 课壳，复制自 `guide/octave-manual` 的壳（保留
   `get_exercises`/`record_attempt`/Octave 复算检查这条线），此后独立演进（ADR 0062）。
   手册同步脚本（`sync_upstream.py`、docstrings 管线）对本应用无用，不复制；公式 KaTeX。
7. **协作**：开 `comms/chen-linear-algebra` 舱（leader zcode，worker cursor）。习题数字
   化采集（底本 PDF → `content/exercises/*.json`，verbatim + locator + Octave 复算）按
   章拆给 worker，任务书写明验收口径；格式以本应用 AGENTS.md 与首批示范章为准。

## 后果

- `guide/` 第一次进中文版权出版物：没有 sync 管线，「上游同步」退化为以底本 PDF 为准的
  人工核对；locator 的页码以纸书页码为准（电子版页码偏移在 AGENTS.md 里写清换算）。
- 原书 156 页、习题总量以实物为准：若某章原书习题不足，宁缺毋滥（ADR 0129），不凑数、
  不用自编题充数；可从例题出 `adapted` 变式并标注。
- 壳上游是 PDF 而非 Git 仓库，`upstream.json` 记书目信息与文件指纹（SHA-256）代替
  pinned commit。
- 学习者本机需装 Octave（命令行版即可，ADR 0057 不兜底安装）；`verify` 复算依赖它，
  没装时 `check.py` 跳过复算但出处检查照跑。
