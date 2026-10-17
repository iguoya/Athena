# T-001 审查报告：工程一致性与官方示例（前十章）

审查人：cursor · 范围：curriculum `order` 1–10 · 尺子：`guide/gtkmm/AGENTS.md`、应用 ADR 0001/0006、根 AGENTS 教学规范（预测–运行）

## 总体结论

1. **第 6 章（按钮）是双轨样板**：`simulation`↔`demo.buttons`↔`exp.buttons` 配对齐全，`--self-check` 具备，演示源码约 100 行（≤150），符合 ADR 0001。
2. **第 7–10 章有官方示例与测验，但没有 Web 模拟 / 真机演示 / 骨架实验**；预测–运行主要靠「节页顶部跑官方示例」（ADR 0008），与第 6 章深度不一致。
3. **`example.frame` 章号与 `page_ref` 错位，按 `App.tsx` 过滤逻辑永不渲染**——清单里有、学习者界面上看不到。
4. **官方镜像抽检**：`exercise/buttons/{button,checkbutton}/main.cc` 与 upstream 同路径文件正文一致；整树 `diff` / `check.py` 因本会话 Shell 钩子全灭未能跑通（见文末「阻塞」）。
5. **壳与前端**：`src/`、`src-tauri/` 未见按章手写整页或 Rust 内嵌课树文案；示例区与模拟均为清单/块类型驱动。

## check 输出摘要

**未能执行** `python scripts/check.py gtkmm`。

原因：本机 Cursor Shell 的 `beforeShellExecution` 把 Claude Code 的 PreToolUse 钩子（`.claude/settings.json` → `block_bulk_git_add.py`）用 **PowerShell** 语法注入后交给 **bash** `eval`，命令未启动即被拒。子代理 / best-of-n 同样失败。

待恢复 Shell 后应重跑；静态阅读 `guide/gtkmm/scripts/check.py`：会校验 `demo_ref` 配对、`page_ref`∈全课表节 id、演示孤儿闭环、`--self-check` 编译。**注意**：`page_ref` 只验「是否存在于全课表」，**不验是否属于 `translation_ref.chapter` 对应章**——故 `example.frame` 能过 check、仍在 UI 消失（见发现 F1）。

辅助脚本已放：`comms/gtkmm-review/artifacts/cursor/_audit.py`（恢复 Shell 后在仓库根执行）。

## 对账结果（demos.json ↔ curriculum 前十章）

| 章 order | id | 章 status | 模拟/演示/实验块 | 清单 demos/exps | examples（translation_ref.ch） |
|---:|---|---|---|---|---|
| 1 | chapter-introduction | translated | 仅 quiz | — | — |
| 2 | chapter-installation | translated | 仅 quiz | — | — |
| 3 | chapter-basics | translated | 仅 quiz | — | — |
| 4 | changes-gtkmm3 | pending | 无 KP | — | — |
| 5 | changes-gtkmm4 | pending | 无 KP | — | — |
| 6 | chapter-button-widget | translated | sim×2 + demo + exp + observation | demo.buttons, exp.buttons | buttons×5 |
| 7 | chapter-range-widgets | translated | 仅 quiz | — | range_widgets |
| 8 | chapter-misc-widgets | **pending**（各 page 多为 translated） | 仅 quiz | — | entry/frame/infobar/label/progressbar/spinbutton/tooltips |
| 9 | chapter-container-widgets | pending | 仅 quiz | — | actionbar/aspectframe/… |
| 10 | chapter-listmodel | pending | 仅 quiz | — | listmodelviews×… |

- **悬空 theory_refs**：前十章范围内 demos/experiments 的 `theory_refs` 均指向 `gtkmm.buttons.*`，存在于课表。
- **重复 id**：清单内未见重复（抽检 demos/experiments/examples id 前缀分域）。
- **page_ref**：除 F1 外，抽检 ch6–10 的 `page_ref` 均落在前十章某节 id 上；无 `page_ref` 的章级示例（如 `example.buttons.scalebutton`、`listbox_flowbox.listbox/listmodel`、`listmodelviews.editable_cells`）符合 ADR 0006「章级展示」约定。
- **课表引用闭环**：前十章内唯一 `demo_ref`/`exp` 引用为 `demo.buttons` / `exp.buttons`，均在清单中。

## 官方示例镜像

| 项 | 结论 |
|---|---|
| upstream 路径 | `guide/gtkmm/upstream/gtkmm-documentation/examples/book/` **可读**（gitignore，Glob 扫不到，Read 可读） |
| 抽检一致 | `buttons/button/main.cc`、`buttons/checkbutton/main.cc`：exercise ≡ upstream（全文一致） |
| 整目录 diff | **待查**（需 Shell：`git diff --no-index`）；脚本 `_audit.py` 可批量 sha256 |
| exercise 禁止改 | 本次只读，未改 |

## 模拟 ↔ 真机配对

| 模拟（`src/simulations.tsx`） | curriculum `demo_ref` | 清单 | `--self-check` | 行数 |
|---|---|---|---|---|
| `signal-flow` | demo.buttons（push-button KP） | 有 | `demos/buttons/src/main.cpp` L70–79 | ~100 |
| `toggle-state` | demo.buttons（toggle KP） | 有 | 同上 | 同上 |
| （仅此二种） | — | demos[] 仅一条属前十章 | exp.buttons 亦有 self-check L55–64 | lab 骨架短 |

无「有模拟无演示」条目。前十章也无「有演示无模拟」清单条目（仅 buttons）。

## 前端 / 壳疏失

- `App.tsx` L650–655：示例过滤 = `translation_ref.chapter` ∧ (`!page_ref` ∨ `page_ref===page.id`)——内容驱动，无按章手写页。
- `src-tauri`：路径、spawn、进度；错误字符串为运维提示，未见课树/讲解文案进 Rust。
- 未发现为某章定制的整页组件。

## 预测–运行（ADR 0113）

| 章 | 先预测再运行的落点 |
|---|---|
| 1–3 | 仅 quiz；无 demo/sim/example → **只有文档+测验** |
| 4–5 | 空章（pending） |
| 6 | sim → demo → observation_quiz → exp：完整 |
| 7–10 | 节顶官方示例可跑 + quiz；**无** sim/demo/exp |

## 发现表（按严重度）

### F1 · P1 · `example.frame` 永不显示

- **证据**：`content/demos.json` L261–277：`translation_ref.chapter=8`，`page_ref="sec-single-item-containers"`。
- 课表：`sec-single-item-containers` 属于 **order 9** `chapter-container-widgets`（`curriculum.json` L1636–1639），**不在** order 8 的 `pages`（L1385–1421）。
- 过滤：`src/App.tsx` L651–654 要求章号与 `page_ref` 同时匹配 → 第 8 章各节 `page.id`≠该 ref；第 9 章章号≠8 → **两侧都不渲染**。
- **建议**：按官方归属把 `translation_ref.chapter` 改为 `9`（Frame 属单子控件容器），或去掉错误 `page_ref` 改章级（仍挂 ch8 则需确认正文是否真有 Frame）。改前对照 upstream 该示例在文档中的章。

### F2 · P1 · 第 7–10 章缺少演示/模拟配对（相对 ADR 0001 / 主原型）

- **证据**：`curriculum.json` 中 `type":"simulation"|"demo"|"experiment"` 仅出现在按钮章（约 L908–938、L1004）；Grep 全文件仅此四处。
- `demos.json` 的 `demos`/`experiments` 数组在前十章范围内只有 buttons 两条。
- 第 7–10 章虽有官方示例，但无 Web 模拟、无带协议的真机演示、无骨架实验。
- **建议**：若主原型要坚持到控件各章，至少为 Adjustment 联动（ch7）、常用容器布局（ch9）各补一对 sim+demo；否则在章说明里显式降级为「以官方示例为运行端」，避免学习者期待与第 6 章同构。

### F3 · P1 · 第 1–3 章无任何「运行」锚（示例/演示均无）

- **证据**：demos.json examples 的 `translation_ref.chapter` 均 ≥6；课表 1–3 仅 quiz 块。
- 基础章（信号、Hello World）最需要预测–运行，却只有测验。
- **建议**：为 `sec-helloworld` / `sec-signals-overview` 挂官方 basics 示例（若 upstream `examples/book` 有对应集），或最小 `demo.basics`；结构性取舍交 leader。

### F4 · P2 · 章级 `status` 与页级不一致

- **证据**：order 8/9/10 章 `status:"pending"`，但下属多数 `pages[].status:"translated"`（如 L1378–1421、L1627–1646、L1809–1858）。
- check 对「章已译」口径若看章 status，会与页现实不符。
- **建议**：页全译后把章 status 升为 `translated`，或文档写清章 status 另有含义。

### F5 · P2 · 迁移章 4–5 空壳

- **证据**：L809–846：`knowledge_points:[]`，`checkpoint:[]`，page pending。
- 主线含迁移章（ADR 0003）合理；前十章审查范围内记一笔：无测验无演示，学习闭环空。
- **建议**：保持空可以，但导航上勿暗示「已可学完」。

## 结构建议（不改 id；交 leader 裁决）

1. check.py 增加：**examples 的 `page_ref` 必须属于 `translation_ref.chapter` 对应 section 的 pages**（堵住 F1 类漏洞）。
2. 是否要求第 7+ 章补 demo 轨道，还是正式宣布「仅第 6 章做双轨样板、其后以官方示例为运行端」。
3. Frame 归属：改清单章号 vs 改课表——以官方 DocBook 章节为准。

## 阻塞（未能 `status review`）

| 项 | 状态 |
|---|---|
| `inbox` / `status doing` / `status review` | 未跑（Shell 钩子） |
| `scripts/check.py gtkmm` | 未跑 |
| exercise↔upstream 整树 diff | 未跑（抽检 2 文件一致） |

**请 leader（claude-code）**：1) 修复 Cursor 对 `.claude/settings.json` PreToolUse 的 PowerShell 包装（或本机 bash 会话绕过），以便 worker 能跑 `comms.py`/`check.py`；2) 将本任务标 `blocked` 或在钩子修复后让本会话/新会话续跑补证据后转 `review`。

P0 条数：0 · P1 条数：3（F1–F3）· P2 条数：2（F4–F5）
