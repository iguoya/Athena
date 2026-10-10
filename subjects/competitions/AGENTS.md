# Athena 赛历 — 项目协作规则

本文档是 **`subjects/competitions` 独立应用** 的项目级指令。仓库根 `AGENTS.md` 写各应用
共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **图谱/参考类应用**（主仓库 ADR 0114）：呈现竞赛清单供查阅与决策——谁能参加（在校生 /
  社会人士）、属于什么方向、和 Athena 里哪门课对得上。不判分、不建进度库、不建
  `content-contract.json`，跨应用教学规范对本应用不生效。
- 启动器「大赛」圈的首个成员。某个赛事要做真题训练时，按「一个赛事一个应用」另建学习
  应用（ADR 0114 决策 4），**赛历本身不长出练习功能**。

## 数据纪律（本应用的核心约束）

赛历是事实性信息，错一条资格就可能让人报不上名或错过比赛。

- 唯一数据源是 `content/competitions.json`，字段含义写在文件头的 `_` 里。
- **资格必须带核对信息**：`verify.level` 为 official / notice / report 时必须有 https 来源与
  `YYYY-MM-DD` 核对日期；查不到当届或往届条款的一律 `pending`，`students` / `public`
  也写 `pending`，**不凭印象写 yes**。
- 例外只有「以单场规则为准」的平台（天池、Kaggle）：写 `per-event`，并在 note 里说明。
- `url` 只填确认过的官网，不确定留 `null`；宁缺不错。
- 核对超过一年的条目界面会标「可能过期」，届时重新核对，改 `verify.date`，而不是静默沿用。
- `courses` 只写 Athena 课程的**显示名**，不引用别的应用的路径、id 或代码（ADR 0032）。
  课程改名时这里同步改显示名。

`scripts/check.py` 机器校验上述规则（取值枚举、来源与日期、https、方向引用、id 唯一）。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust），只开窗口并通过 `tauri-plugin-opener` 把官网交给系统浏览器；
  没有自定义命令。
- **界面**：Vite + TypeScript，无框架。数据在构建期由 Vite 直接打进前端——一份几十条的
  JSON 不值得走一趟运行期读取。
- 端口 1502，进程 `athena-competitions`。

## 开发与验证

```sh
launcher open competitions
python3 scripts/check.py competitions        # 数据校验 + 前端构建 + cargo check
```

只改了数据时加 `--skip-rust`。
