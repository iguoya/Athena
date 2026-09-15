# ADR 0002：桌面用 Tauri；公众号只做只读导出

- 日期：2026-09-13
- 状态：已接受
- 取代：口头比较过的 Flutter / uni-app / 小程序做题方案

## 背景

本应用要同时满足：电脑上做句子和短文；必要时把讲解同步到微信公众号自己看；
以后可能有一个手机阅读壳。作者排除了「手机上做题」。

Flutter 能一份 UI 打桌面和手机，但对长文划词、中文输入、以及 Markdown→HTML→
公众号这条管线并不更省事。本仓库已有 `apps/dsa` 的 Tauri 2 + TypeScript 实践。
Markdown 的设计目标就是 HTML；Tauri 的界面是系统 WebView，和短文渲染、公众号
导出同路。Flutter 要把 Markdown 另译成 Widget，再为公众号另做一条 HTML 管线。

公众号图文会去掉 JavaScript，本来就不能跑做题页。个人主体账号自 2025 年 7 月起
也不能用发布接口自动群发，最多推草稿箱再手动点发布。

## 决策

1. **交互应用用 Tauri 2 + Vite + TypeScript**，目录为 `apps/english/`。壳要薄：
   Rust 只负责内容路径、SQLite 进度和日后的发布辅助；课树与文案不进 Rust。
2. **不引入 Flutter、Electron、小程序做题页、手机 App。** 手机若只要看，用公众号
   图文（或日后同一份内容生成的静态页）即可。
3. **进度库自建自管**（对齐主仓库 ADR 0037）：
   `<data_dir>/AthenaEnglish/learning.db`，无条件建表。知识点 ID 前缀 `en.`。
   接受并忽略 `--store`，以免旧主程序传来时进程直接退出。
   > **位置已由主仓库 ADR 0053 修订**：改写 `progress/learning.db` 并随仓库走，
   > 上面那个用户数据目录只在发行副本里使用。
4. **与主程序零编译耦合。** 不读 `resources/athena.json`，不链接主程序代码，
   不进主程序 Meson / `scripts/check.sh`。`app.json` 仅供可选的进程发现。
   英语二不是计算机 / 电子信息学科图谱上的实践科目，**本期不往首页路线图挂节点**；
   需要时另改主程序 `domain_graph`。
5. **Markdown 只用于可阅读正文**（短文、策略讲解）。题目、选项、答案、义项、
   先修、到期复习全部用 JSON。禁止把整本课写成一篇 `.md`。
6. **公众号是单向发布，不是第二运行时。** `tools/publish/` 把讲解和精读收成
   HTML / 草稿；不在微信里判分。发布器可以后做，但内容模型必须现在就允许同一份
   `content/` 被导出。个人号自动发布能力弱，按「生成草稿、手动点发布」设计。

## 后果

- 和 `apps/dsa` 同一套肌肉：`npm run tauri:dev` 即可开发。
- 放弃「一份 Dart 打两端」；手机阅读若以后要做成独立壳，再评估 Tauri Mobile
  或静态站，不回溯改课表。
- 桌面 WebView 在各系统上的细微差异可接受；英语二用不到像素级跨端一致。
