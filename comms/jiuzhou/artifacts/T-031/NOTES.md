# T-031 首屏体验 · 交付

## 测量方法
- 浏览器前台；`Network.setCacheDisabled` + 硬刷新 `http://localhost:1516/`。
- `performance.now()` 自模块加载起，至 `idle` 且 `land-fill` `queryRenderedFeatures` > 0。
- 读 `__jzDebug.bootMs()` / `mapPaintReady()`。

## 前后对比
| | 前（eager 学术 JSON） | 后（按需切片 + 骨架） |
|---|---|---|
| 主包 `App-*.js` | ≈ 3.00 MB | ≈ **898 KB** |
| 学术层 | 打进主包 | 按年动态 `import` 分片（见 build 日志 xixia/qin/han-…） |
| 冷启动首绘 | Claude 实机：数秒海色底无陆地、无提示 | 本机测得 **1607 ms** 陆地已绘；≤3 s 目标 |
| 加载态 | 无 | 地图区「铺陈海陆与疆域…」骨架，首绘后淡出 |

## 改动
1. `academic-layers.ts`：`import.meta.glob` 去掉 `eager`；`academicAtYearAsync` / `academicBelongingAtAsync`。
2. `App.tsx`：按年异步灌学术面；点击归属异步；`mapPaintReady` 骨架；`document.hidden` 时不提前揭（配合 T-030）。

## 截图
- `after-first-paint-1607ms.png`：首绘完成后（陆地+疆域+标签齐）
- 启动瞬间仍有应用级「载入地图…」；地图内骨架在 React 挂载后、idle 前出现。

## check
`python scripts/check.py --skip-rust` 绿。
