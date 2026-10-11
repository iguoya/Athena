# ADR 0131：共享层放 `shared/`，以 gtkmm 试点

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：共享层放 `shared/`；试点选 gtkmm）
- 延续：[ADR 0130](0130-shared-build-and-schema.md) 决策 7 的前两项（位置、试点）；
  工具选型细节与公共 schema 终稿仍待定（见决策 5）
- 关联：[ADR 0129](0129-prefer-quality-over-quantity.md)、[ADR 0037](0037-independent-apps-own-their-progress-store.md)

## 背景

ADR 0130 立了「构建共享、schema 共享」的方向，位置与试点未定。事实核查：

- **漂移已经发生在最简单的表上。** `gtkmm` 的 `attempts` 是
  `(knowledge_id, item_id, correct, answered_at)`；`software`/`embedded` 的 `attempts` 是
  `(course, chapter_id, kp_id, question_id, correct, mode, answered_at)`；`design-patterns`
  用的是 `knowledge_progress` / `lab_progress` / `lab_draft` / `quiz_picks`，`updated_at` 还是
  TEXT；`c-plus-plus` 另有 `run_history`、`ai_insight`。同一个概念「一次作答」有三种形状。
- **gtkmm 适合当试点**：Tauri 2 + React + TS，与多数应用同栈；Rust 侧仅 `lib.rs` 一个
  文件、451 行，进度层只有 `attempts`、`my_translations` 两张表；已有 69 条真实作答；
  内容充实（302 个内容文件）；档位 `open`，不阻断出处检查，试点出问题不会卡住考试类应用。
- 样本小意味着迁移风险小，但同时也意味着它的需求面窄——所以 schema 终稿不由它单独定
  （决策 4）。

## 决策

1. **共享层放仓库根的 `shared/`。** 与 `subjects/`、`practice/`、`launcher/` 平级，不属于
   任何应用，不出现在启动器里（没有 `app.json`，不是应用，也不算素材坑）。
2. **`shared/` 按语言/用途分子目录，每个包自带版本号**，起步只建试点要用的：
   - `shared/progress/`：Rust crate，负责进度库的建表、迁移、作答写入与读取接口；
   - 其余（TS 阅读/测验组件、内容契约公共部分）等试点跑通、第二个应用要用时再建，
     不预建空目录（宁缺毋滥，ADR 0129）。
3. **试点应用为 `subjects/gtkmm`。** 试点范围只有一步：把 `gtkmm` 的进度层（`lib.rs`
   中的建表、写作答、读进度）换成引用 `shared/progress`，对外行为不变。用 Cargo 的
   `path` 依赖引用，不引入根级 workspace——应用仍然可以单独构建，共享层缺席时报错信息
   要指向 `shared/`。
4. **公共进度 schema 的起点与冻结条件。**
   - 起点：以「一次作答」为核心表，字段取现有三种形状的并集的最小可用部分：
     应用/课程标识、知识点 ID、题目/条目 ID、是否正确、模式、时间戳（统一为 INTEGER
     Unix 秒）、与现有 `app_settings` 的键值表。
   - 在 `gtkmm` 试点期间它是**草案**；冻结前必须用 `software`/`embedded` 的 `attempts`
     与 `design-patterns` 的 `knowledge_progress` 做一次字段对照，确认公共部分覆盖得了、
     应用特有字段有扩展位。
   - 现有数据必须无损迁移：`gtkmm` 的 69 条作答随迁移带进新表，迁移前打 tag 并在提交
     信息写明回退办法（ADR 0129 决策 3）。
5. **仍待后续决定**（不在本 ADR 范围，也不得由代理自行决定）：
   - TS/前端侧共享采用哪种工作区工具（`ascent` 用 pnpm，其余用 npm）；
   - `driver`（Flutter + 中心 PG）是对接还是排除出共享层；
   - 试点之后的推广顺序。
6. **验收**：`python3 scripts/check.py gtkmm` 通过；`gtkmm` 能在迁移后的库上启动、
   读到原有 69 条作答；`shared/progress` 自带单元测试覆盖建表、幂等迁移、作答写入。

## 后果

- 根 `AGENTS.md` 与 `docs/REPOSITORY.md` 的仓库结构图新增 `shared/`；结构卫生检查的根目录
  白名单（`scripts/check.py` 的 `_ROOT_ALLOW`）需登记它。这两处随试点的第一个提交一起做。
- `shared/` 的改动门槛高于单个应用：改动前跑全量 `scripts/check.py`，不止试点应用。
- 试点成败的判据是迁移后的行为与数据，不是代码行数下降。若发现公共 schema 覆盖不了
  现有形状，回到本 ADR 修订决策 4，而不是在 `shared/` 里硬凑。
