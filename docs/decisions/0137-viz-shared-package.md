# ADR 0137：可视化呈现件抽成 `packages/viz`——C 档的明示例外，同类功能只留一份实现

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：选「C 档例外」；「能共用的功能就独立抽取，本质上他们都属于课程应用」；
  「模拟器公用代码出现了很多份，一定要抽出来公用，省得维护多份类似功能的代码」）
- 草稿：[STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V1（按 [ADR 0134](0134-structural-decisions-cold-down.md) 先草拟、复看后落）
- 例外于：[ADR 0135](0135-share-low-cost-build-layer-first.md) 决策 5「不建 `shared/`，不抽代码」与 C 档；
  满足 [ADR 0132](0132-defer-shared-layer.md) 决策 5 的第二条重启条件——某项通用能力要在多个应用同时落地，
  逐个重做的成本明显超过抽取
- 衔接：[ADR 0136](0136-unify-on-pnpm.md)（pnpm，B 档的前置）；[ADR 0133](0133-heterogeneous-stack-admission.md)
  （默认栈）；[ADR 0032](0032-independent-apps-launched-as-processes.md)（独立应用）

## 背景

1. **同一份呈现代码在多个应用里整份重复。** 实测（2026-10-11）：`trace-player.ts`（步进回放器，
   185 行）在 algorithms、cs408、data-structures、design-patterns、linux、organization
   六个应用里各一份，与 data-structures 的版本相差 **8 行，全是解析前缀**（`#ds-trace` /
   `#algo-trace`…）与对应的一行注释；其样式（`.trace-*`）在各应用的 `styles.css` 里同样逐份相同。
2. **同一概念跨框架重写。** 进程状态图在 software（React，101 行）与 embedded（Vue，126 行）
   各写了一遍。
3. **表现形式相同、数据来源不同。** gtkmm 的手写 `setTimeout` 模拟器与 trace-player 都是
   「逐帧点亮」，区别只在帧是脚本给的还是真实进程打印的。
4. 这些应用本质上都是**课程应用**：讲解、可视化、实验的形态同类，同类功能必然反复出现。
   逐个应用各写一份，修一个 bug 要改 N 处，N 份还会各自漂移。

## 决策

1. **原则：同类功能只留一份实现；课程应用之间能共用的功能，独立抽取成公共件。**
   本篇把原则落到**可视化呈现件**；其余 C 档内容（阅读器、测验、复习、进度表、内容块、
   `content-contract`）不因本原则自动放行，仍按 0132 的重启条件逐项评估。
2. **例外范围写死：不触及 schema、内容块、进度库、应用文案的纯呈现件。** 满足即可入包；
   任何一项不满足则留在应用内。本例外不得作为 C 档其他内容的先例。
3. **位置与包名：仓库根 `packages/viz/`，包名 `@athena/viz`，纯 TypeScript 源码，不预编译**
   （消费方的 Vite 直接吃源码）。不建 `shared/`（0131 的位置仍不执行）；`packages/` 目前只为本例外而设。
4. **挂接：各应用 `package.json` 写 `"@athena/viz": "link:../../packages/viz"`**（pnpm 的符号链接，
   改包源码即时生效）。B 档工作区建成后改写为 `workspace:*`，**应用侧 import 路径不变**。
   消费方需把 `packages/viz` 加进 Vite 的 `server.fs.allow`（默认不放行工作区之外的文件）。
5. **准入纪律：**
   - **props-only**：不 import 任何应用的内容契约、进度库、文案；与应用的耦合只通过参数。
   - **二次使用才升入**：单应用独有的组件先留在应用内，第二个应用确实要用时再抽，接口由两个
     真实使用方定形。例外：已有多份拷贝的（如 trace-player）直接抽。
   - 概念专属的模拟器（如 gtkmm 的「clicked 信号的旅程」）留所属应用，只复用其下的通用件。
   - 样式随组件走：包内带 `.css`，颜色等取自消费方已有的 CSS 变量（`--surface`、`--primary`…）；
     各应用的变量名目前一致，不一致时由消费方在自己的主题里补齐，不在包里写死色值。
6. **框架：core 与 DOM 回放器不依赖框架。** trace-player 是原生 DOM 实现，React/Vue 都能直接用；
   框架绑定等有两个以上同框架使用方时再做，不预建。
7. **首批只收 `trace-player`**：解析前缀改为参数；帧渲染器可按 `kind` 注册扩展，内置 `list`；
   未知 `kind` 仍降级为原始 JSON（沿用 data-structures ADR 0004 的前向兼容约定）。
8. **迁移顺序：先 data-structures 试点**，验证 `install → dev → build → tauri dev` 全通；
   再 algorithms、cs408、design-patterns、linux、organization **逐个迁移，每个独立提交**。
   试点之前不批量改。
9. **防回流检查**：`scripts/check.py` 增两条——(a) 根目录白名单登记 `packages`；
   (b) 应用 `src/` 内出现与公共包同名的拷贝（如 `trace-player.ts`）即报错。
10. **「独立可运行」的含义不变：不依赖其他应用。** `packages/viz` 不是应用，同在仓库内，
    克隆即有；构建时被打进各应用的产物，发行包不受影响。各应用 `AGENTS.md` 里
    「不依赖任何其他应用即可构建」一类措辞，在迁移该应用时补一句「公共呈现件取自 `packages/viz`」。

## 后果

- 六份 `trace-player.ts` 与对应样式收敛为一份；修改回放器只改一处，六个应用同时受益。
- 改 `packages/viz` 会同时影响所有使用方，**改动前后必须跑所有使用方的构建**（`check.py` 逐应用跑）。
  这是共享的固有代价，用迁移完成后的检查与独立提交来控制。
- 0135 决策 5 对本例外松一格，其余不变；根 `AGENTS.md`、`docs/REPOSITORY.md`、`docs/decisions/README.md`
  的措辞随之更新（索引行与「通用应用代码待……再议」一句）。
- 未覆盖：software 的 `viz/`（React）与 embedded 的 `ProcessStates.vue`（Vue）重复的进程状态图——
  跨框架，需另评估是否抽 core + 两个薄绑定；gtkmm 模拟器接真机 `signal` 事件作帧源，同样另议。
- `main.ts`（五个应用 2357 行近乎整份拷贝）属阅读/测验应用代码，仍归 C 档暂缓，不在本篇范围。
