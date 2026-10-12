# esd ADR 0002：前端由 Vue 3 迁到 React，界面体验差异原样保留

- 日期：2026-10-11
- 状态：已接受（使用者 2026-10-11：「所有的 Tauri + Vue 技术路线的应用，也采用摘星的技术路线，保持底层构建的统一」）
- 依据：仓库 [ADR 0138](../../../../docs/decisions/0138-course-apps-unify-tauri-react.md) 决策 2、3
- 修订：本应用 [ADR 0001](0001-split-from-softcert-vue-stack.md) 决策 2 的「Vue 3 技术栈」部分；0001 的拆分决定、
  「与 softcert 两种成体系体验」的意图不变

## 背景

0001 选 Vue 3 是为了让 embedded 与 softcert（现 software，React）在**技术体系**上也不同，好做对比。仓库随后把课程类应用
统一到 Tauri 2 + React，页面渲染以摘星为基线（仓库 ADR 0138）：同一概念的组件与模拟器不再按框架各写一份，
也不再多养一套 Vue 工具链。本应用是第二个有实质代码的 Vue 应用（约 2400 行），其余 Vue 应用是空壳或已先迁出。

## 决策

1. **前端改为 React 19 + TypeScript + Vite + Tailwind v4**，动画用 Motion（`motion/react`）、图标用 `lucide-react`、
   公式仍用 katex；`cn()`（clsx + tailwind-merge）按摘星基线引入。
2. **体验差异不动**：AGENTS.md「界面组织」列的四条差异（顶部指挥台、学习路径时间线、行动面板首页、阅读器 + 键盘作答）
   是产品决定，与实现框架无关，迁移后逐条保留。「与 softcert 刻意不同」现在只指界面与交互，不再指技术栈。
3. **内容与进度零改动**：`content/` 全部 JSON 与教材原文、`content-contract.json`、`progress/learning.db`、Rust 侧
   `src-tauri/`（`record_attempt`、`attempts_summary`、`today_stats`、`load_setting`、`save_setting`）、知识点前缀
   `esd.` 一律不动；`src/content.ts`、`src/db.ts`、`src/types.ts`、`src/theme.ts`、`src/textbook-text.ts` 是纯 TS，
   原样保留。
4. **viz 注册表契约不变**：`src/viz/index.ts` 仍以 `"component-name": 组件` 的形式登记，`scripts/check.py` 解析该文件做
   内容对账；组件类型由 Vue 的 `Component` 换成 React 的 `ComponentType<{ params }>`。
5. **皮肤 utility 登记进 tailwind-merge**：`style.css` 里的 `accent-gradient`、`accent-soft`、`accent-fg`、
   `text-gradient`、`tk-card`、`tk-display` 是纯 CSS 类，tailwind-merge 默认会把 `accent-*` 当成 accent-color 工具类
   合并掉，`cn()` 因此要把它们登记成独立类组（见 `src/lib/utils.ts`）。

## 后果

- 删除全部 `.vue` 与 `vue-tsc`，`package.json` 去掉 vue、motion-v、lucide-vue-next、@vitejs/plugin-vue、vue-tsc。
- `pnpm build` 改为 `tsc && vite build`；`scripts/check.py` 流程不变。
- 仓库级 `STACK_VERSIONS` 里 Vue 相关两项（`@vitejs/plugin-vue`、`vue-tsc`）此后无应用使用，可删。
