# Athena English — 项目协作规则

本文档是 **`apps/english` 独立应用** 的项目级指令。本应用与 Athena 主程序
（GTK / Meson / `resources/athena.json`）**平级、可脱离**：不读主程序配置、
不链接主程序代码、不依赖主程序进程即可完成开发、构建与练习全流程。

主仓库根目录的 `AGENTS.md` 只描述主程序与「异构应用」边界；**改本应用时以
本文为准**。可选地，主程序可通过 `app.json` 把本应用当独立进程拉起
（主仓库 ADR 0032），那不是运行本应用的前提。

## 定位

- 目标：通过**考研英语二**。主练**句子**和**短文**，并强化英语二词表范围内的
  词在语境中的认识（ADR 0001）。
- **但界面上不出现「考研」「英语二」这类考试字样**：窗口标题、课表标题、按钮和
  提示一律叫「英语自学」，用「初级 / 中级 / 高级」表达进阶。考试目标只写在
  `docs/decisions/` 和本文里，不写进用户看得见的文案。
- 做题只在桌面进行；手机 / 公众号只看，不判分（ADR 0002）。
- 不以通用学英语、口语听力、整卷模考或专业英语为目标。

## 技术栈（本应用自有）

- **壳**：Tauri 2（Rust）
- **界面**：Vite + TypeScript（Web UI，非 GTK，非 Flutter）
- **内容**：`content/curriculum.json` + `content/vocab|sentences|passages/`
- **进度**：SQLite，写入用户数据目录 `AthenaEnglish/learning.db`，自建表、
  自迁移（主仓库 ADR 0037）。`--store` 仅为兼容而接受并忽略。
  知识点 ID 前缀一律 `en.`。

不引入主程序的 Meson、gtkmm、Blueprint、`athena.json`。

## 目录与所有权

| 路径 | 职责 |
|---|---|
| `content/` | 课表、词表、句子、短文；**唯一内容源** |
| `src/` | 前端：能力路线 / 练习台 / 错题本（ADR 0005） |
| `src-tauri/` | 窗口、读内容、进度与复习 |
| `bin/athena-english` | 稳定入口脚本（给可选的主程序 discover） |
| `app.json` | 仅供主程序发现；本应用不依赖它才能开发或运行 |
| `tools/publish/` | 日后把讲解导出为公众号草稿；本期可空 |
| `docs/decisions/` | 本应用 ADR |
| `AGENTS.md` | 本文 |

## 内容与教学分层

精神对齐「大纲 → 讲解 → 练习」，载体与主程序无关。课表唯一源是
`content/curriculum.json`。

- 词必须带义项和例句，禁止「单词 = 一个中文」。
- 句子练习问切分、指代或句意，不考语法名称本身。
- 短文用 Markdown 正文 + JSON 题目，挂在需要成篇语境的轨上（`track.passage`），
  篇幅短于真题阅读篇。
- 作文只机检字数下限和 `required_any` 里的连接方式；组织和用词由作者对照
  `reference` 与 `checklist` 自己看，不进掌握度（ADR 0004）。
- 掌握度只由做题结果写入，禁止手动标记熟练。
- 编写时优先对照和例句，不堆长文（ADR 0003）。

当前主线是三个等级，每级同练三条轨（ADR 0004）：

| 等级 | 单词 | 例句 | 作文 |
|---|---|---|---|
| 初级 | 高频词义与搭配 | 主干、因果、转折、指代 | 仿写与扩写成段 |
| 中级 | 一词多义与抽象搭配 | 一到两层从句、让步 | 观点 + 理由 + 收束 |
| 高级 | 熟词生义与立场词 | 短文里恢复主干与态度 | 限时完成任务回应 |

## 架构原则

- **独立可运行**：`npm run tauri:dev` / `./bin/athena-english` 不经过主程序。
- **内容驱动 UI**：改课优先改 `content/`，不为新节复制整页。
- **壳要薄**：Rust 侧负责路径、进度；业务文案与课树不进 Rust。
- **与主程序零编译耦合**：主程序 Meson / `scripts/check.sh` 不构建本应用。

## 开发与验证

```sh
cd apps/english
npm install
npm run tauri:dev      # 日常开发
npm run build:app      # 产出 bin 入口可用的本地二进制
./bin/athena-english
```

环境变量 `ATHENA_ENGLISH_ROOT` 可强制指定应用根目录（含 `content/`）。

验证以本目录为准：前端 `npm run build`、Rust `cargo check`（在 `src-tauri`）。
**不必**为改本应用而跑主仓库 `scripts/check.sh`，除非同时改了主程序 discover。

## 修改流程

1. 改课：先改 `content/`，再补前端展示类型（若有新练习形态）。
2. 改运行时：只动 `src-tauri`，保持命令表面稳定。
3. 改 UI：只动 `src/` + `index.html`。
4. 需要主程序图谱入口时，另提主仓库 `domain_graph` 变更（本期不挂）。
