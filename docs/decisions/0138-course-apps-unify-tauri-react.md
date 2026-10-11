# ADR 0138：课程/讲解/演示类应用统一 Tauri 2 + React，页面渲染以摘星为基线，schema 不动

- 日期：2026-10-11
- 状态：已接受（tiger 2026-10-11：「迁移所有的课程类、讲解类、演示应用，全部采用一致的技术底层框架 Tauri + React，
  不符合的全部改造，采用统一的构建规范和依赖规范」；澄清「用 Tauri」「machine 先改，c-plus-plus 与 driver 暂缓」
  「共用 schema 太暴力，时机未到，先维持现状」「页面渲染以摘星为基础」）
- 草稿：[STRUCTURE-PROPOSALS.md](../STRUCTURE-PROPOSALS.md) V2（按 [ADR 0134](0134-structural-decisions-cold-down.md) 先草拟、复看后落）
- 修订：[ADR 0133](0133-heterogeneous-stack-admission.md)——默认栈对课程/讲解/演示类由「默认」升为「强制」；
  machine 从准入表与「历史例外」中退出（改造，见决策 7）
- 取代：[ADR 0042](0042-c-language-qt-qml-lessons.md) 决策 1、3（machine 的 Qt Quick / QML 壳与 QML 热加载）；
  决策 2（`playground/` 的 LVGL 小程序保留）与决策 4（共用教学规范）不变
- 延续：[ADR 0135](0135-share-low-cost-build-layer-first.md) B 档、[ADR 0136](0136-unify-on-pnpm.md)（pnpm）、
  [ADR 0137](0137-viz-shared-package.md)（`packages/viz`）
- 不变：[ADR 0132](0132-defer-shared-layer.md)（schema 与内容抽象暂缓）、[ADR 0129](0129-prefer-quality-over-quantity.md)
  （`id` 不改嫁）、[ADR 0062](0062-apps-own-their-constraints.md)

## 背景

实测（2026-10-11，25 个 Tauri 课程/图谱应用 + 3 个非 Web 栈）：

1. **前端框架三分天下。** Tauri + React 12 个，Tauri + 原生 TS 8 个，Tauri + Vue 5 个；另有 machine（Qt6/QML）、
   c-plus-plus（GTK）、driver（Flutter）。Tauri + Vue 的 firmware、microcontroller、rtos 只是约 50 行的空壳。
2. **原生 TS 里有一整族同源壳。** algorithms、cs408、data-structures、linux、organization 的 `main.ts` 各约 2357 行，
   两两只差约 22 行，是同一份代码复制了五次。
3. **同类功能反复实现。** 进程状态图在 React（software）与 Vue（embedded）各写一遍；ADR 0137 已把步进回放器抽成
   无框架公共包，但框架不统一，上层封装仍要各写各的。
4. **0133 只管了「新应用默认什么」，没管「存量怎么办」。** 它把 Vue 与原生 TS 壳留在了规则之外，
   把 machine 的 Qt 记为不得效仿又不迁的历史例外。

## 决策

1. **适用范围**：学习应用与图谱/参考类（REPOSITORY.md 的前两类），即以讲解或演示为目的、被启动器当课程应用打开的那批。
   `practice/` 与素材坑不在内，自由发挥。
2. **技术底座强制统一为 Tauri 2 + React + TypeScript + Vite。** Vue、手写 DOM 的原生 TS 壳、Qt/QML 壳不再允许；
   存量按决策 6 逐波改造。Electron 不进课程类（实践类 c-gui-lab 不受约束）。
3. **页面渲染技术以摘星（ascent）为基线**：Tailwind v4、shadcn/ui 式组件（`class-variance-authority` + `clsx` +
   `tailwind-merge`）与 `lucide-react`、Motion、Zustand、React Router；图表与富文本按需用 ECharts / Tiptap；
   ESLint、Prettier、Vitest；TypeScript 固定 6.x。
   - **只定技术，不定视觉**：配色、字体、皮肤各应用自便。
   - **摘星自身不动**：其 ADR 0066（不趋同）仍管摘星自己；此处是其他应用向它的渲染栈看齐。
   - **shadcn/ui 的组件源码各应用自己生成**；等第二个应用要用同一组件时再抽进 `packages/`
     （沿用 ADR 0137 的「二次使用才升入」纪律），不预建 UI 组件库。
   - `packages/viz` 保持无框架 TS，React 应用挂一层薄绑定；ADR 0137 里「Vue 绑定」一项作废。
4. **schema 不动。** 每个应用继续读自己的 `curriculum.json` / `course.json` / `content-contract.json`，进度库表结构、
   知识点前缀不变，不借迁移对齐字段。迁移只换**呈现层**：把手写 DOM 或 Vue 改成 React 组件，内容格式原样保留。
   0132 的暂缓范围原样有效。
5. **共享配置（0135 的 B 档）按「课程属性」准入。**
   - **课程属性 = 同时具备四要素**：章节、随堂练习、课后习题、章节技术实验；按应用在自己 `AGENTS.md` 里**声明**的教学结构
     判定，不按当前已写内容（刚落骨架的课程设计上就是这套结构，算在内）。
   - 符合者采用共享配置：pnpm 工作区、`catalog:` 统一依赖版本、共享 `tsconfig` / `vite` 基础配置。
   - 不符合者（目前：polaris、math-tools、competitions）仍须 Tauri 2 + React，依赖版本继续守 0135 A 档，
     但不入工作区、不强制套共享基础配置。
   - **本条只定准入判据与目标形态，不定试点。** 0135 要求先在一个应用上跑通 `install → dev → build → tauri dev`
     再批量；试点应用与启动时机暂不定（现有 React 课程应用多为空壳，缺乏有分量的试点），定下后另记。
6. **迁移先易后难，逐应用单独提交，逐波由使用者指派启动**：
   firmware、microcontroller、rtos（空壳重建）→ competitions、math-tools → embedded →
   五份同源壳（algorithms、cs408、data-structures、linux、organization）→ machine → design-patterns、mathematics。
   每个应用验收：`pnpm typecheck`、`pnpm build`、`tauri dev` 能跑，`scripts/check.py <id>` 通过；`content/` 与 `progress/`
   的 git diff 为空；迁移前后同页截图对照；应用内不再遗留 `.vue`、手写 DOM 壳或 QML。
   同源壳的试点应用暂不定。迁移前打 `pre-react-unify` tag。
7. **machine 退出异构准入并改造**：由 Qt6/QML 改为 Tauri 2 + React。细节记在 machine 自己的
   [ADR 0008](../../subjects/machine/docs/decisions/0008-migrate-shell-to-tauri-react.md)。LVGL `playground/` 保留不动。
8. **c-plus-plus 与 driver 本轮暂缓**：这是使用者对范围的暂缓，不是新的准入。重启条件：使用者另行指派；
   届时 c-plus-plus 按「GTK 是教学内容的原生载体」重评，driver 按存量成本重评。gtkmm 前端本就是 Tauri + React，
   其 CMake 实验是教学内容，不受影响。
9. **检查**：`scripts/check.py` 新增一条跨应用检查——课程/讲解/演示类应用的前端必须是 React。
   豁免表带理由逐项列出尚未迁移的应用与暂缓项，**每迁完一个就删一行**，表空即全部统一；
   检查随首个迁移波一起加，不提前红。

## 后果

- 「默认栈」从倾向变成规则；Vue 与原生 TS 壳此后不得再新增。
- 同一概念的组件与模拟器不再需要按框架各写一份，ADR 0137 的公共包有了单一的上层封装目标。
- 内容格式仍各自演进，将来重启 schema 议题时，以事实上已共用同一套课表与进度库的原生 TS 一族为起点
  （调研记录见草稿 V2），而不是以任何现有 React 应用为起点。
- 需随首个迁移波同步的文档：根 `AGENTS.md` 与 `docs/REPOSITORY.md` 的技术栈措辞、`docs/ENGINEERING.md`、
  各被迁应用 `AGENTS.md` 的技术栈节与目录表、`scripts/check.py` 与 CI（machine 的 Qt 步骤随 machine 迁移删除）。
- 风险：design-patterns 与 mathematics 的壳最重，机械移植也要数天，故放最后；手写 DOM 改 React 易丢键盘、
  滚动位置、焦点等交互细节，靠截图对照与逐页清单兜底；迁移期间被迁应用应由单一代理负责，避免与内容改动撞车。
