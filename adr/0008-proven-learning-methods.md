# 0008 借鉴公认有效的学习理论

- 状态：已采纳（由 ADR 0014 补充）
- 日期：2026-09-30
- 决策人：tiger

## 背景

tiger 希望把互联网上其他高效的英语学习思想融入软件背后的指导思想。

## 决策

采用以下与本项目原则一致的方法，每条都落到具体功能上：

| 思路 | 在软件里怎么用 |
| --- | --- |
| 可理解输入（Krashen） | 选文按她的生词量分级，难度只比她高一点 |
| 四条路径（Nation, 2007） | 听读写加上鼓励性的说；生词只占很小比例；每周限时重读旧内容练流利度 |
| 注意假说（Schmidt, 1990） | 点句子彩色标出结构、高亮生词 |
| 输出假说（Swain） | 写每天必做；AI 批改指出与地道说法的差距 |
| 跟读（Shadowing） | "说"这一步用逐句跟读，作为鼓励项 |
| 提取练习（Roediger & Karpicke, 2006） | 复习一律挖空填词，配合 FSRS 间隔算法 |
| 词块法（Lewis） | 生词本可以收整个词块，不只收单词 |

英语很大程度上是记忆学习，所以还采用以下记忆科学：

| 思路 | 在软件里怎么用 |
| --- | --- |
| 间隔效应（Ebbinghaus, 1885） | 生词和句式用 FSRS 安排在快要忘记时复习 |
| 双重编码（Paivio） | 每个词和句子都配朗读音频和场景插图 |
| 生成效应（Jacoby, 1978） | 先看英文释义猜词义；复习填空；每天自己造句 |
| 加工层次（Craik & Lockhart, 1972） | 造句题让她写自己的生活，不写空泛的句子 |

Krashen 的理论有争议（只靠输入不够），所以和输出假说、四条路径一起使用。

出处：

- https://en.wikipedia.org/wiki/Input_hypothesis
- https://www.hackingchinese.com/analyse-and-balance-your-chinese-learning-with-paul-nations-four-strands/
- https://en.wikipedia.org/wiki/Noticing_hypothesis
- https://en.wikipedia.org/wiki/Comprehensible_output
- https://contact.teslontario.org/wp-content/uploads/2018/08/Hamada-Shadowing.pdf
- https://en.wikipedia.org/wiki/Testing_effect
- https://en.wikipedia.org/wiki/Lexical_approach
- https://en.wikipedia.org/wiki/Spacing_effect
- https://en.wikipedia.org/wiki/Dual-coding_theory
- https://en.wikipedia.org/wiki/Generation_effect
- https://en.wikipedia.org/wiki/Levels_of_processing_model

## 后果

- 调度逻辑需要记录她的生词量和已遇到的语法点，才能选出难度合适的文章。
