# softcert ADR 0001：嵌入式课程拆出，声明重组豁免（ADR 0080 首批第二例）

- 日期：2026-10-09
- 状态：已接受（使用者明确决定拆分）
- 基线：tag `pre-softcert-reorg`
- 依据：仓库级 [ADR 0090](../../../../../docs/decisions/0090-softcert-splits-esd.md)、
  [ADR 0080](../../../../../docs/decisions/0080-reorg-exemption-when-intent-changes.md)

## 意图改了什么

本应用从「软考中级备考，两门课程（软件设计师、嵌入式系统设计师）共用起步」
收窄为「软考中级·软件设计师单科备考」。课程维度与「一门课程一个目录」的
组织方式保留，将来可加软考其他方向；嵌入式系统设计师整体迁出到新应用
`subjects/esd`（ADR 0090）。

## 豁免范围

仅本次拆分，允许：

1. 删除 `content/esd/` 课程目录（course.json、chapters、quizzes）、
   `content/textbooks/esd2ed/` 教材、`past-exam-esd-*` 真题卷及嵌入式专属
   sources 登记——不是废弃，是整体迁入 `subjects/esd`，在基线 tag 处可取回。
2. `courses.json` 删除 `esd` 课程条目；前端删除对应导入、课程数据与嵌入式
   专属文案（一年一考等）。
3. 随内容迁出的知识点 id 前缀改写：`sc.esd.*`、`sc.os.rtos` 在新应用内改为
   `esd.*`（softcert 无 `learning.db`，从未有作答数据挂在旧前缀上）。

## 不因此放宽

- 出处要求（ADR 0043、0089）：判分题目必须带 `source`，真题年份与题号严禁
  凭记忆编造，检查照跑。
- 语义基准：菜单目录对齐官方教材、考纲对齐、分值驱动，`swd` 侧一律不动。
- 评级规范（难度/掌握目标/类型/先修）与篇幅校准规则照旧。
