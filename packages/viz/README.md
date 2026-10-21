# @athena/viz

课程应用共用的**可视化呈现件**（[ADR 0137](../../docs/decisions/0137-viz-shared-package.md)）。
同类功能只留一份实现。

## 收什么、不收什么

- 收：不触及 schema、内容块、进度库、应用文案的纯呈现件，props-only。
- 不收：阅读器、测验、复习、进度表（仍按 ADR 0132 暂缓）；概念专属的模拟器留所属应用。
- 第二个应用确实要用时才升入；已有多份拷贝的（如 `trace-player`）直接抽。

## 现有内容

| 件 | 作用 |
|---|---|
| `trace-player` | 消费真实进程打印的 `<marker> {...}` 快照行，逐帧回放；`kind` 渲染器可扩展 |
| `archive-panel` | 历史归档条目（ADR 0176）：多文件只读代码视图 + 行级批注 + 一键运行原代码；读文件与运行通过 `deps` 回调交给应用，样式 `archive-panel.css` |

## 使用

```jsonc
// 应用 package.json（pnpm 符号链接；B 档工作区建成后改 "workspace:*"）
"dependencies": { "@athena/viz": "link:../../packages/viz" }
```

```ts
import { parseTrace, mountTracePlayer, stopTracePlayback } from "@athena/viz";
import "@athena/viz/trace-player.css";

const frames = parseTrace(stdout, "#ds-trace"); // marker 由应用自定
```

Vite 默认不放行工作区之外的文件，应用的 `vite.config.ts` 需要
`server.fs.allow` 包含本目录。

## 修改纪律

改本包会同时影响所有使用方：改动前后跑**所有**使用方的构建。
