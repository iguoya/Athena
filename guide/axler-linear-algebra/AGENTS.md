# Athena Axler 线性代数精读 — 项目协作规则

本文档是 **`guide/axler-linear-algebra` 独立应用** 的项目级指令，不依赖任何其他应用即可完成
开发、构建与学习。仓库根 `AGENTS.md` 写各应用共同遵守的规则；**改本应用时以本文为准**。

## 定位

- 目标：**精读 Axler《线性代数应该这样学（第四版）》（Linear Algebra Done Right, 4e）官方
  中文版**，学「以线性映射/算子为中心」的定理型线代。作者 Sheldon Axler，译者吴俊达、
  何阳，作者官网开放获取，341 页。应用形态是 `guide/` 圈的教材精读（主仓库 ADR 0179；
  形态判据同 ADR 0143、0162、0163、0177），「数学」圈。
- **底本即中文**（官方中文版）：没有翻译管线（不同于 selinger/siefken/octave-manual）。
  章导学自编，重心在**原书习题与证明思路**。
- 与 `guide/` 其他应用**互不引用**。

## 出处（本应用最重的一条规则）

- 出处档位 `open`（主仓库 ADR 0089：不对着外部考试），但**题源是应用级硬门禁**
  （ADR 0179 决策 2，沿 chen-linear-algebra 的先例）：
  - 每道入库题目必须带 `source_refs`，`relation` 只许 **`verbatim`**（原书习题原样）或
    **`adapted`**（以原书题为底改问法，`note` 写明改动点）。
  - `locator` 必须给到**原书印刷页码与题号**，如「p.9 习题 1A 9」「p.20 习题 1C 5」。
    页码以 PDF 页眉的原书印刷页码为准，换算：**PDF 0-based 页号 − 13 = 印刷页码**
    （如 PDF 第 23 页是印刷页 10）。
  - **`authored`（自编题面）不入题库**；`scripts/check.py` 见到 authored 直接报错。
  - 原书公式在 PDF 里提取出来是乱序的：按原书重排 LaTeX，`note` 注明「公式重排」——
    内容同一，仍是 verbatim。原书笔误照录并加注，不改原文。
  - **判分选项是应用自设的教学层**：`verbatim` 题的 `note` 必须声明「判分选项为应用
    自设」，正确项的依据是原书定义与定理，不冒充原书内容（ADR 0179 决策 4）。
- 不凭印象伪造出处；locator 写不出来就说明题还没核对过，不入库。
- 题面语义有疑义时以**英文原版**为准（英文版暂未入库，见 `upstream.json` 的
  `english_edition`）。

## 底本（`upstream/`）

- `upstream/线性代数应该这样学-第四版-官方中文版.pdf`：作者官网开放获取的官方中文版
  （<https://linear.axler.net/LADR4eChinese.pdf>，2024-08），SHA-256 记在 `upstream.json`，
  `scripts/check.py` 核对完整性。它是全部 verbatim 出处的最终核对物。
- 全书 9 章 + 附录；章目录以实物 PDF 书签核对（2026-10-21），不用二手资料。

## 学习方法与界面

- 方法原型（主仓库 ADR 0113）：主**问题解决**（证明题按「目标—已知—桥」拆解），辅
  **辨析决策**（概念真伪辨析——原书大量 verify/判断类习题）。
- **判分只做 choice**：证明对错无法机判，判分动作是思路选择与概念辨析；证明本身先自己
  写，再对照 `sol` 自评，不进进度库（ADR 0179 决策 3、4）。没有 Octave/数值复算线。
- 内容薄厚分层（主仓库 ADR 0164）：`stage: 2` 的块默认折叠进「进阶」。
- 不用「显然」「容易看出」等把难度推给读者的词（检查会拦，主仓库 ADR 0013）——这条对
  讲定理的书尤其要紧，原书直译里的这类措辞在导学与解答里改写成有内容的说法。

## 技术栈（本应用自有，最初复制自 `guide/chen-linear-algebra` 的壳并去掉 Octave 复算线，
此后独立演进）

- **壳**：Tauri 2（Rust）：`get_curriculum` / `get_section` / `get_exercises` / `get_figure` /
  `record_attempt` / `get_attempts`；界面 Vite + React + TypeScript，公式 KaTeX。
- **内容**（全部手写，无生成器）：`content/scope.json`（范围：已收哪些章）↔
  `content/curriculum.json`（课表，两者须一致）；`content/sections/<章id>.json`（章导学）；
  `content/exercises/<章id>.json`（原书习题）。逐章扩充时四处同步（含 COVERAGE.md 状态列）。
- **进度**：SQLite，`AthenaAxlerLinearAlgebra/learning.db`，不进 git，由启动器同步（主仓库
  ADR 0155）；`attempts` 事件表 append，「最近一次」按 `answered_at` 认，不按自增 id。
- **知识点前缀 `axler.`**：作答记录的 `knowledge_id` = 章 id（如 `ch1`）。
- dev 端口 **1530**；进程 `athena-axler-linear-algebra`；环境变量
  `ATHENA_AXLER_LINEAR_ALGEBRA_ROOT`。

## 题目写法

- 题 `id` 用原书编号：习题 1A 9 → `ex1a-9`，第 4 章习题（无节字母）3 → `ex4-3`，字母
  小写（正则 `ex\d[a-f]?-\d+[a-z]?`）。
- `stem`：中文照录官方中文版，可含 `$公式$`、`$$展示公式$$`、`` `代码` ``、围栏代码块。
- `check.kind` 只收 `choice`：恰好 1 个 `ok`，每个选项都有 `text` 与 `why`；干扰项取
  真实的概念混淆点（同域假设、集合包含当子空间、标量直觉等），不凑数。
- `sol`：参考解答写证明的「目标—已知—桥」与关键步骤，证明之外给出「这题在练什么」。

## 开发与验证

```sh
launcher open axler-linear-algebra        # 日常开发
python3 scripts/check.py                  # 结构、题目出处门禁、底本校验、公式、构建
python3 scripts/check.py --skip-rust      # 跳过 cargo check
```
