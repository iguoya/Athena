# esd ADR 0001：从 softcert 拆出独立成应用，采用 Vue 3 技术体系

- 日期：2026-10-09
- 状态：已接受（使用者明确决定）
- 关系：仓库级 [ADR 0090](../../../docs/decisions/0090-softcert-splits-esd.md)；
  出处档位 [ADR 0089](../../../docs/decisions/0089-source-tiers-by-app-nature.md)；
  技术体系参照 `subjects/math-tools`

## 背景

本应用的内容（嵌入式系统设计师课程、官方教材第 2 版 OCR、2010–2020 历年真题卷）
原是 `softcert` 里的 `esd` 课程。使用者决定软考拆成两个应用：softcert 保持 React
界面体系承载软件设计师，嵌入式独立出去换一套技术体系，获得不同的使用体验；
两应用都挂启动器「软考」分组。

## 决策

1. **id `esd`**：嵌入式系统设计师的通行缩写（Embedded System Designer），与内容
   里沿用至今的 `esd-` 章节 id 同源。进程/二进制 `athena-esd`，dev 端口 1480，
   identifier `cn.athena.esd`，窗口标题「嵌入式系统设计师」。
2. **技术栈 = math-tools 那套**（使用者点名要不同体验）：Tauri 2 + Vue 3 +
   TypeScript + Vite + Tailwind 4 + motion-v + lucide-vue-next；皮肤机制同构——
   一套组件、`--tk-*` 令牌换氛围，三套浅色皮肤（电路/晨读/草稿），localStorage
   存偏好。公式渲染用 katex（内容块里有 LaTeX）。
3. **但它是学习应用，不是工具**：与 math-tools 的本质差异是教学规范全部生效——
   Rust 侧带 `progress/learning.db`（rusqlite bundled，与 softcert 的 store 同构，
   掌握度只由作答写入）、章节考核与历年真题演练、考试档出处契约
   （`content-contract.json`，tier exam）。
4. **知识点前缀 `esd.`**（如 `esd.mcu`、`esd.os.rtos`）：从 softcert 迁出时由
   `sc.esd.*` / `sc.os.rtos` 改写——softcert 尚无进度库，改写零数据损失，
   `sc.` 前缀的语义是 softcert，不随内容带走。基线在 softcert 仓库的
   tag `pre-softcert-reorg`。
5. **内容边界**：`content/esd/`（章树、章节、考核）、`content/textbooks/esd2ed/`、
   `content/past-exams/`（11 份 esd 卷 + 导入管线说明）与嵌入式专属来源登记。
   考核题当前 16 题为 adapted/authored 存量，属考试档欠账：契约
   `blocking: false` 并备注，替换为对应章节真题精选后改回 `true`。
