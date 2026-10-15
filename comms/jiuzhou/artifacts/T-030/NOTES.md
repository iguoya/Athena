# T-030 打磨与稳健 · 交付

## 1. 学术层不透明度滑块
- 侧栏「精度」下新增「学术层透明度」0–150%，默认 100%（×1，保持原 0.2 / 近似 0.14）。
- 截图：`academic-opacity-40.png`（40%）、`opacity-slider-ui.png`。

## 2. 切年份保持视图
- 年轴 scrub / `__jzDebug.setYear` **只改年，不改选中事件**。
- 取景 `useEffect` 用 `frameKeyRef`（`selectedId|axis|territoryMode`），领土 GeoJSON 随年刷新不再 `fitBounds`/`flyTo`。
- 点事件 / 切轴 / 故事 / 点地点仍取景（T-027 快照逻辑保留）。

## 3. 派生文件过期检测
- `scripts/check.py` → `check_derived_geo()`：
  - `content/territories.json` 新于 `packages/maps/geo/territories-clipped.json` → 报错并提示 `clip_territories.py`
  - `build_base_layers.py` 新于 `land.json` → 报错并提示重跑
- 本机：`territories-clipped / land.json OK`（见下）。

## 4. `__jzDebug.rendered` 隐藏态
- `document.hidden === true` 时返回 `null`（不再返回 0）。
- 实现：`App.tsx` 内 `rendered` 开头判断。

## check
```
python scripts/check.py --skip-rust
# atlas OK → derived geo freshness OK → layers OK → tsc+vite build OK → smoke OK
```
