---
id: T-007
title: 彩色地形底图（Natural Earth I 栅格）
owner: cursor
status: done
priority: P1
depends: T-001
created: 2026-10-13 22:43
updated: 2026-10-14 08:32
---
## 目标（已改版：从“灰度晕渲”升级为“彩色地形”）
使用者反映地图太单调简陋。没有山，“关中四塞”“蜀道难”就看不见；而且现在只有米色和灰青两种颜色。经调研：Natural Earth 的 **NE1_50M_SR（Natural Earth I with Shaded Relief）** 是按土地覆盖着色的彩色地形图——绿色低地、黄褐山地、带山影——一张图就能让底图既好看又有地理信息。详见 `docs/DESIGN-REFERENCES.md`。

## 做法
1. 下载（公域，官方站点；下载前请在其 terms of use 页面核对公共领域条款并记入 README）：
   `https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/50m/raster/NE1_50M_SR.zip`（约 39MB，放 `.cache/maps/natural-earth/`，**不入库**）。
2. 写 `packages/maps/scripts/build_relief.py`：裁到 70–145°E / 5–55°N，缩到宽约 2400px，输出 WebP（质量约 80），**≤3MB**，写入 `packages/maps/geo/relief.webp` 并附 `relief.json`（四角坐标）。大图原件不入库。
3. 渲染：作为 MapLibre `raster` 图层，放在海面之上、疆域色块之下；**用图层自带的 `raster-saturation` / `raster-hue-rotate` / `raster-contrast` / `raster-brightness-*` 调色**（偏暖、略降饱和以与纸本风格协调），**不要对整个地图容器加 CSS filter**（每帧合成，开销大）。
4. 陆地矢量面（T-001）保留，用作海陆遮罩：海面盖在 raster 之上并只覆盖海，使海岸线锐利。
5. 邻国（朝鲜半岛、日本、越南、中亚）在 raster 上盖一层 25–30% 的纸色半透明，使中国本土更突出。

## 验收
- 缩放 4–7 级：青藏高原、秦岭、太行、横断山、四川盆地、华北平原、长江中下游平原一眼可辨，颜色有绿—黄—褐的层次；
- 首屏资源增量 ≤3.5MB；平移缩放帧率无明显下降（在回报里写你的测量方式与结果）；
- 回报附前后对比截图路径。

## 进展记录
- [2026-10-13 23:02] cursor：todo → doing · 开始：NE 灰度晕渲裁东亚、raster 乘算叠在陆地底
- [2026-10-13 23:04] cursor：doing → review · GRAY_50M_SR_OB 裁东亚→relief-east-asia.webp 0.29MB；image+raster opacity0.35 叠陆面；prepare_relief.py；原 zip .cache。check 绿。
- [2026-10-13 23:13] claude-code：review → doing · 返工：地图图层未渲染（layers()=[]、rendered(land)=0），无法验证；详见 23:2x 消息。
- [2026-10-13 23:44] cursor：doing → review · 静态产物复测图层已画出。rendered(land) 此前为 0 是因为图层 id 是 land-fill，现按源 id 解析。前214 land=28 china=6 territory=4 snaps=qin-215[秦,匈奴] schematic=false；前100 snaps=han-100[西汉,匈奴] territory=4；前150 schematic=true snaps=null territory=2。1440x900 地图画布 800x584。smoke_dist OK。
- [2026-10-14 08:32] claude-code：review → done · 实机验收：彩色地形晕渲已叠在陆面，截图可见
