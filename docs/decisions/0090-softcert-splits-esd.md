# ADR 0090：软考拆成两个应用——软件设计师留 softcert，嵌入式系统设计师独立成 esd

- 日期：2026-10-09
- 状态：已接受（使用者明确决定）
- 关系：应用边界重组，按 [ADR 0080](0080-reorg-exemption-when-intent-changes.md) 走重组豁免
  （softcert 应用级 ADR 0001，tag `pre-softcert-reorg`）；启动器分组机制见
  [ADR 0083](0083-launcher-mind-map.md)；出处分档见 [ADR 0089](0089-source-tiers-by-app-nature.md)

## 背景

`softcert` 以「一门应用承载软考中级备考课程」起步，`courses.json` 注册了
`swd`（软件设计师）与 `esd`（嵌入式系统设计师）两门课程，共用一套 React 界面。
两门考试同属软考中级、共用通过线，但备考节奏、案例形态与一年考次都不同；
softcert 的原规划是继续往里加课程，应用会越长越重。

使用者决定：软件设计师与嵌入式系统设计师分别独立成两个应用，都挂在启动器
「软考」标签下；softcert 保持现有界面体系，嵌入式独立出去并采用 math-tools
那套技术体系（Vue 3），换一种使用体验。

## 决策

1. **`softcert` 保留，承载软件设计师。** id、界面体系、React 技术栈、进度库与
   `sc.` 知识点前缀全部不动；`courses.json` 只注册 `swd`。课程维度保留——将来
   软考其他方向（网络工程师等）仍按「一门课程一个目录」加进这个应用。
2. **新应用 `subjects/esd` 承载嵌入式系统设计师。** 进程 `athena-esd`，dev 端口
   1480，`group` 与 softcert 同为「软考」——启动器按 `group` 字符串归组，共用
   同名分组无需任何 launcher 改动。技术栈采用 math-tools 那套：Tauri 2 + Vue 3 +
   TypeScript + Vite + Tailwind 4 + motion-v，皮肤机制照搬（一套组件、令牌换氛围）。
   它是**学习应用**：进度库 `progress/learning.db`（Rust 侧 rusqlite，与 softcert
   同构）、教学规范与考试档出处要求全部生效。
3. **内容边界按课程切**：`content/esd/`、`content/textbooks/esd2ed/`、
   `past-exam-esd-*` 真题卷与嵌入式专属来源登记迁入 esd；swd 全部留在 softcert。
   真题导入管线（`scripts/import-past-exam.py`、`content/past-exams/README.md`）
   两边各留一份、各自维护。
4. **esd 知识点前缀从 `sc.esd.*` / `sc.os.rtos` 改为 `esd.*`。** softcert 尚无
   `learning.db`，这批知识点从未进过任何进度库，前缀改写零数据损失；`sc.` 的
   语义是 softcert，留给 esd 应用是永久误导。改写在重组豁免范围内，基线在
   tag `pre-softcert-reorg`。softcert 侧 `sc.cs.*`、`sc.os.*` 不动。
5. **两应用构建完全隔离**（ADR 0032、0062）：esd 不引用 softcert 的任何路径或
   配置；两边各自的 `content-contract.json`、`sources.json`、`scripts/check.py`
   独立维护，出处检查（ADR 0043、0089）按考试档各自接入。

## 后果

- `docs/REPOSITORY.md` 结构树与名字表、根 `README.md` 应用表补登 `esd`。
- esd 的章节考核题当前是 adapted/authored 存量（16 题），与 softcert 同属考试档
  欠账：契约 `blocking: false` + 备注写明，替换为真题精选后改回 `true`。
- softcert 首页删除嵌入式专属文案（一年一考等）；「两科同时 ≥45 分通过」是软考
  中级通用通过线，两个应用都保留。
- 两个应用今后各自演化，界面体系不要求对齐——这正是拆分的目的之一。
