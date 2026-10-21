# ADR 0179：新增 `guide/axler-linear-algebra`——Axler《线性代数应该这样学（第四版）》官方中文版精读，定理型线代

- 日期：2026-10-21
- 状态：已接受（使用者指派：「下载目录有本《线性代数应该这样学》的 PDF，以这本书为基础
  编写一个应用，将 PDF 放到该新建项目下目录」；id 与目录名按「作者-课程」惯例定为
  `axler-linear-algebra`）
- 关系：应用形态沿 [ADR 0143](0143-guide-manual-apps.md)（`guide/` 装跟随一本外部手册/
  教材精读的应用）；同圈先例 [ADR 0162](0162-linear-algebra-readers-in-guide.md)
  （selinger/siefken 两本线代教材精读）与 [ADR 0177](0177-chen-linear-algebra.md)
  （chen 精读，本应用壳的来源）；出处分档按 [ADR 0043、0089](0089-source-tiers.md)；
  公域入库按 [ADR 0159](0159-public-domain-by-default.md)；方法原型按
  [ADR 0113](0113-dominant-learning-methods.md)；宁缺毋滥按 [ADR 0129](0129-quality-over-quantity.md)

## 背景

Sheldon Axler《Linear Algebra Done Right》第四版是「以线性映射/算子为中心、推迟行列式」
的定理-证明型线代教材的代表。作者官网对第四版开放获取，并提供官方中文版
《线性代数应该这样学（第四版）》（吴俊达、何阳译，341 页，2024 年 8 月发布，
<https://linear.axler.net/LADR4eChinese.pdf>），使用者已取得该官方中文版 PDF。

`guide/`「数学」圈已有一条定理线代精读先例（selinger/siefken，ADR 0162：工作簿式、
几何直观先行、英文原文 + 自建译文管线）和一条计算路线（chen，ADR 0177：中文原创书、
Octave 复算）。本书补上第三种形态：**定理-证明型教材的中文译本精读**——没有译文管线
（底本即中文），也不以数值计算为主（没有 Octave 复算线），重心是概念辨析与证明思路。

## 决策

1. **新增 `guide/axler-linear-algebra`**，`group` 为「数学」。id 与目录名
   `axler-linear-algebra`（作者姓氏，同 `selinger-`/`siefken-`/`chen-` 惯例）；进程
   `athena-axler-linear-algebra`；知识点前缀 `axler.`；dev 端口 1530；进度库
   `AthenaAxlerLinearAlgebra/learning.db`，`attempts` 表 append（ADR 0037、0155）。
2. **学习应用，出处档位 `open`；题源硬门禁沿 chen 先例**（ADR 0177 决策 2）：每道入库
   题目必须带 `source_refs`——`relation: verbatim`（原书习题原样录入）或 `adapted`
   （以原书题为底改问法，`note` 写明改动点），`locator` 给到**原书印刷页码与题号**
   （如「p.23 习题 1A 9」）；`authored`（自编题面）不入库。页码换算：PDF 重排版页眉印
   原书页码，PDF 0-based 页号 − 13 = 印刷页码，换算式写进应用 `AGENTS.md`。题面语义
   有疑义时以英文原版为准（英文版暂不入库，仅作语义基准）。
3. **方法原型**（ADR 0113）：主**问题解决**（证明题按「目标—已知—桥」拆解，判分动作
   是证明思路/关键步骤的选择），辅**辨析决策**（概念真伪辨析——原书习题大量
   verify/construction 类，正适合做判断题）。**没有真做校验线**：本书不是计算书，
   不复制 chen 的 Octave 复算检查。
4. **判分形态**：证明题无法机判对错，判分动作是自设的思路选择项（`check.kind: choice`，
   恰一个 `ok`，每项带 `why`）。选项是应用自设的教学层，不冒充原书内容——在题目
   `source_refs.note` 里声明「选项为应用自设，题面与正确思路依据原书」。
5. **内容形态**：章节结构跟随原书目录（9 章，以实物 PDF 书签核对，不用二手资料）。
   第一批内容：curriculum 收全书 9 章；第 1 章导学 + 习题 1A/1B/1C 若干 verbatim 入库
   作示范。其余章按宁缺毋滥（ADR 0129）逐章补，不做空骨架。
6. **底本**：官方中文版 PDF 放 `upstream/`（ADR 0159 公域口径，出处照记——作者官网
   开放获取 URL、译者），SHA-256 记 `upstream.json`；它是全部 verbatim 出处的最终
   核对物。
7. **技术栈与壳**：Tauri 2 + React 课壳，复制自 `guide/chen-linear-algebra`（最近的
   同栈先例），去掉 Octave 复算与题目 lint 的真做校验部分，此后独立演进（ADR 0062）。
   公式 KaTeX，界面与进度库通路不变。

## 后果

- `guide/` 第一次进**译本**：chen 是中文原创书、selinger/siefken 是英文原文 + 自建
  译文管线，本应用的底本是别人的译文——题面照录译文（verbatim 的核对物是这份官方
  中文版），语义基准写明是英文原版，将来取得英文版 PDF 再补进 `upstream/`。
- 判分只靠辨析选择，掌握度信号比数值题弱：复习回路由作答记录派生时以「辨析正确率」
  为准；证明能力本身靠学习者对照 `sol` 自评，不进进度库。
- 官网 PDF 是固定发布物（带版本页），无同步管线；若官网更新版本，按「id 不改嫁」以
  新提交替换底本并在 `upstream.json` 记版本变更。
