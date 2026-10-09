# ADR 0098：连线最小化——非必要不特意连线

- 日期：2026-10-10
- 状态：已接受（tiger 直接指示）
- 关系：修订 [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md) 决策 4 的
  承接表达；思维导图连线语义仍按 [ADR 0083](0083-launcher-mind-map.md) 与
  [ADR 0092](0092-launcher-tree-attach-and-softcert-rename.md)

## 背景

tiger 指示（2026-10-10）：独立并行的应用之间非必要不特意连线。esd↔softcert 的
related 已按此删除（前一个提交）；本条把同一原则应用到其余清单声明。

「必要」的判断：连线表达**从属或配套**（挂靠线 parent、配套工具 related）时有
语义；表达「并列相关」「历史演进」时，同领域圈与名字已经足够，特意画线是噪音。

## 决策

1. **删除 `english.related = ["ascent"]`**：磨砚与摘星是并列的独立英语应用
   （ADR 0020、0066），同属「英语」领域圈已表达兄弟关系。
2. **删除 `cpp.evolves_from = "machine"`**：「C 与机器」与「C++ 教程」各自独立
   成课，C→C++ 的历史渊源不构成界面上的连线理由。
3. **删除 `dsa.parent = "softcert"`**：数据结构与算法是正牌独立学科（与摘星、
   磨砚平级），挂靠线暗示了从属，不合适。它承接软件设计师第 3、8 章编码实验的
   分工**不变**（ADR 0092 决策 4），但表达降为内容指引——softcert 课程树在这两
   章写「去 dsa 做实验」，不靠视觉连线。
4. **保留**：math-tools↔mathematics 的 related（配套工具的附属语义）；c-gui-lab、
   pocket-cube 的 parent 挂靠（tiger 明确要求的从属表达）。
5. **挂靠深度为一层**：所有节点尽量避免一个节点关联多层——不允许链式挂靠
   （A 挂 B、B 又挂 C）；布局实现把「挂靠者自己也是挂靠节点」的解析回退为普通
   节点，防御性杜绝深层嵌套。

## 后果

- 思维导图上的连线只剩两类：领域结构的虎头线/分支线，与少量挂靠线；演进线、
  related 线在当前清单下不再出现。
- softcert 内容建设到第 3、8 章时记得放 dsa 实验指引（content-plan 已有分工）。
