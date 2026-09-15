# ADR 0003：题目必须能指到法条或标准

- 日期：2026-09-15
- 状态：已接受
- 影响：`content/questions/`、`content/sources/catalog.json`、`content-contract.json`
- 对齐：主仓库 ADR 0043

## 背景

驾考商业题库版权不明，不能整库搬进来。道路交通安全法、实施条例、公安部令第
162 号和 GB 5768 是可以核对的公共规则。把口诀题当真相，一旦和条文冲突，题库
就不可信。

## 决策

1. 每道计入掌握度的题都带 `source_refs`，字段名与仓库统一：`relation`、
   `source_id`、`locator`、`url`、`note`。
2. 内容来源只用 `quoted` / `adapted` / `authored`。自造必须说明为什么没有现成
   条文，且同一文件内不得超过一半。
3. 标志题按 GB 5768.2 的形状与颜色分类改写（`adapted`），界面自绘，不附标准
   图样复印件。
4. 接入 `content-contract.json`，`blocking: true`。仓库根的出处检查失败即失败。

## 后果

- 题量会明显小于商业 App。这是有意的：先有能核对的题，再按章扩充。
- 模拟考在题库短于考场题量时折合百分制，不假装已经覆盖全国题库。
