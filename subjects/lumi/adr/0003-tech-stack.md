# 0003 技术栈：Tauri 2 + React

- 状态：已采纳
- 日期：2026-09-30
- 决策人：tiger

## 背景

考虑过 Vue 3 和 React。Vue 只是旧 VuePress 站点留下的历史选择，不构成约束。本项目的第一要务是界面美观、有动效，并且由 tiger 一个人维护四年。

## 决策

| 层         | 选型                            |
| ---------- | ------------------------------- |
| 桌面壳     | Tauri 2（Rust）                 |
| 构建       | Vite                            |
| 界面       | React + TypeScript              |
| 样式与组件 | Tailwind CSS、shadcn/ui         |
| 动画       | Motion                          |
| 图表       | ECharts                         |
| 批注编辑器 | Tiptap                          |
| 状态与路由 | Zustand、React Router           |
| 本地数据   | SQLite                          |
| 工程规范   | pnpm、ESLint + Prettier、Vitest |

- 不使用 Vue。
- 选 Tauri 而不是 Electron：安装包和内存占用小得多，以后还能出手机版；代价是系统层用 Rust，界面跑在 Windows 自带的 WebView2 上。

## 后果

- React 的动效、组件和 AI 相关生态更大，AI 辅助写 React 代码也更可靠。
- 旧的 VuePress 作文站不再继续开发，范文作为内容素材迁移（见 ADR 0010）。
