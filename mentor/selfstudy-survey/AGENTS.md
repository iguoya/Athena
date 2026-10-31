# Athena 自考专业调查 — 项目协作规则

本文档是 **`mentor/selfstudy-survey` 独立应用** 的项目级指令。仓库根 `AGENTS.md` 写各应用
共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **图谱/参考类应用**（主仓库 ADR 0144、0186）：调查 2025–2026 年全国各省计算机类（0809）、电子信息类
  （0807）自考本科的开设格局、主考院校、课程计划、实践环节、教材大纲、报考毕业条件与变动，供查阅与比较。
  不教课、不判分、不建进度库、不建 `content-contract.json`，跨应用教学规范对本应用不生效。
- **不替人选专业**：只列事实对照与取舍维度，不下推荐结论（事实随省份与个人背景差异巨大，唯一推荐会误导；
  与数学罗盘「给唯一路径」不同，见 ADR 0186 后果）。
- 范围钉死在 ADR 0186 决策 2：本科；0809、0807 为核心，0808 作对照；0806 电气类不收。新增专业先改 `scope.json`。
- 协作：采集由协作舱 `comms/selfstudy-survey/` 组织（leader claude-code，worker zcode）；采集规程与数据模型见舱内
  `artifacts/claude-code/DESIGN.md`，先读它再动 `content/`。

## 数据纪律（本应用的核心约束）

- 数据在 `content/`：`scope.json`（范围）、`courses/<成员>.json`、`textbooks/<成员>.json`（分片，读取时合并，同键须同内容）、`athena-map.json`、`provinces/<id>.json`
  （一省一份，含考试院、考期、政策、开设、计划、变动）。
- **每条事实带 `verify`**：`official`（省考试院或主考院校原文）/ `notice`（教育部考试中心、考试院主管的官方门户）/
  `report`（第三方自考网，只作线索）/ `pending`。非 `pending` 必须有 https 来源与 `YYYY-MM-DD` 核对日期（核对当日）；
  `pending` 不得带来源或日期。**课程表、教材、政策、考期只收 official / notice**；`report` 级只能出现在开设记录的线索里。
- **查不到就标待查，绝不凭印象、邻省、往年推断补空**；同一专业同一省版本看不出的写「未标注」，并在 `note` 说明。
  「经核实不开设」（`status: none`）也要有来源，并在 `note` 写清依据（例如「全省开考课程表未列此专业」）。
- **核对义务**：每个考期（4 月、10 月）换版，核对超过一年的界面标「可能过期」。`scope.json` 的 `updated` 与
  `catalog.verified` 是范围层面的核对记录；单条数据的可信度只看它自己的 `verify.date`。
- 官方不公布的（通过率、难度）**不采集、不引用第三方估算**。
- `courses` 的 Athena 对应（`athena-map.json`）只写 Athena 课程的显示名，不引用别的应用的路径、id 或代码（ADR 0032）。
- 原始证据（页面文本快照、PDF）放协作舱 `artifacts/<成员>/evidence/`，**不进应用目录**；应用里只放结构化结论加来源链接。
- 采集的课程行逐行抄自官方课程表；官方原表没有直接给出的量（例如按调整通知核算的总学分）要在 `rules` 里写明是核算值。

`scripts/check.py` 机器校验上述规则（枚举、引用、verify 级别与来源日期、课程代码与名称对账、教材引用、省文件集合、
禁用占位字样）。内容对不对靠 leader 抽查原文逐条核对，不凭记忆。

## 技术栈（本应用自有）

- **薄壳**：Tauri 2（Rust），只开窗口，并通过 `tauri-plugin-opener` 把来源链接交给系统浏览器；数据在构建期由 Vite
  打进前端，无自定义命令、无运行期内容读取、无进度库（模式与赛历、数学罗盘同源，配置骨架最初复制自
  `mentor/mathematics-compass`；此后独立演进）。
- **界面**：Vite + React 19 + TypeScript + Tailwind v4（渲染按摘星基线，ADR 0138；颜色走 `src/styles.css`
  令牌，深色随系统偏好）。九个视图：总览（省 × 专业开设矩阵与覆盖进度）、专业（跨省课程对比矩阵）、省份、课程、教材、
  实践环节、变动、待人工核实（`content/pending.json`：代理查不到、需要人确认的缺口与采集排期，每项写明缺什么、
  试过什么、建议怎么查）、方法与来源。覆盖不全时如实显示「待查」，不隐藏缺口。
- 端口 1535（hmr 11535），进程 `athena-selfstudy-survey`，`group` 为「自考」，更新器 endpoint `selfstudy-survey.json`（ADR 0172）。

## 开发与验证

```sh
launcher open selfstudy-survey
python3 scripts/check.py               # 数据校验 + id/端口对账 + 前端构建 + cargo check
python3 scripts/check.py --data-only   # 采集时自查
```

只改了前端或数据时加 `--skip-rust`。图标改动后跑 `.cache/cargo-target/release/launcher icons` 重新生成位图（ADR 0065）。
