# ADR 0035：把 GTK 的表达上限用满，自绘层迁向 `Gtk::Snapshot`

- 日期：2026-09-12
- 状态：已接受；先在需要动画与聚焦的视图落地，存量 Cairo 绘制按需迁移
- 延续：ADR 0024（内容由 GTK 控件承载）、ADR 0033（大纲与教学过程用活的可视化和互动）
- 不修订：ADR 0024 的技术栈边界——本 ADR **不引入新依赖、不更换 UI 技术栈**

## 背景

ADR 0033 把"数据驱动"和"可互动"定为首选表达方式，要求切换对照、逐步推进一个语义
过程、点节点聚焦一条路径。这些都是**过渡与合成**动作，而当前实现手里只有 Cairo。

盘点了一遍，GTK4 的能力有相当一部分从没碰过：

| 能力 | 仓库现状 |
|---|---|
| `Gtk::Snapshot`（GSK 场景图） | 0 处 |
| `Gtk::GLArea`（GPU / shader） | 0 处 |
| CSS `transition` / `animation` | `resources/style.css` 里 0 处 |
| `Gtk::Revealer`、`Stack` 过渡动画 | 0 处 |
| `Gdk::Texture` 预渲染缓存 | 0 处 |

实际在用的是 4 处 `set_draw_func`（`knowledge_graph_view` 的边、`domain_graph_view`
的边、`chart_view` 的环形图与直方图）加 3 个学习页里的 `DrawingArea`（路线图、值类别
矩阵、类型推导图），全部是 Cairo CPU 绘制；唯一的动画是 `pocket_cube_page.cc` 里用
`add_tick_callback` 手写的转动帧。

Cairo 画静态图形没有问题，但它没有合成层：要让一条路径高亮而其余虚化，只能整幅重画；
要做两种写法的淡入淡出对照，只能自己插值再逐帧重绘。**这不是 GTK 的上限，是我们没有
用到的那部分。**

## `Snapshot` 到底能给什么——先说清楚，免得误解

`Gtk::Snapshot` **不是"更强的 Cairo"**。它是场景图的组装接口：把绘制结果打包成节点树
交给 GSK 合成，节点不变的部分可以被缓存和复用。它本身**没有路径绘制 API**。

gtkmm 4.22 实际绑定出来的 `append_*` 只有八个：`append_cairo`、`append_color`、
`append_layout`、`append_texture`、`append_scaled_texture`、`append_inset_shadow`、
`append_outset_shadow`、`append_paste`。C API 里的渐变和 fill/stroke 路径节点**没有
C++ 包装**，不要按 C 文档去写。

真正的收益在 `push_*` 这一侧：`push_opacity`、`push_blur`、`push_cross_fade`、
`push_mask`、`push_clip`、`push_rounded_clip`、`push_blend`，以及 `translate` /
`rotate` / `scale` 变换栈。

所以结论是：

- **画什么**——曲线、贝塞尔边、弧线、渐变，仍然是 Cairo 的活，通过
  `append_cairo(bounds)` 拿到 `Cairo::Context` 照旧画。
- **怎么合成、怎么动**——透明度、虚化、交叉淡入、遮罩、圆角裁剪、位移与缩放动画，
  交给 `Snapshot`，不要再自己在 Cairo 里手算。

## 决策

### 1. 需要过渡或聚焦的绘制，用 `Snapshot`

自定义 `Gtk::Widget` 子类并 override `snapshot_vfunc()`，在里面用 `push_*` 组织层次，
用 `append_cairo()` 落具体图形。触发条件是这个视图需要以下任意一种：

- 两种状态的**对照切换**（`push_cross_fade`）
- **聚焦一条路径**、其余降权（`push_opacity` / `push_blur`）
- **逐步推进**一个语义过程（变换栈 + 逐帧 progress）
- 元素的**选中 / 悬停**层次（`append_outset_shadow`）

### 2. 纯静态图形继续用 `DrawingArea` + Cairo

`Gtk::DrawingArea` 的 `set_draw_func` 内部本来就走 snapshot 再 `append_cairo`，静态图
迁过去只是换个写法，没有收益。**不做无收益的机械迁移**——不要为了统一风格把现有
四处 `set_draw_func` 全改掉。

### 3. 文本优先 `append_layout`

`render/cairo_text.cc` 的 `draw_cairo_text` 已经走 Pango（Cairo toy API 在 macOS 上画
中文会掉成方块）。在 `Snapshot` 里直接 `append_layout(layout, color)` 把 Pango layout
交给场景图，比再开一层 Cairo surface 省一次合成。存量 `draw_cairo_text` 保留给仍在
Cairo 里的绘制。

### 4. 动画用 `add_tick_callback` 驱动 progress，不自己定时器

`pocket_cube_page.cc` 的做法是对的，保留为参考：tick 回调里推进一个 0→1 的 progress，
`queue_draw()` 触发重绘，在 `snapshot_vfunc` 里把 progress 喂给 `push_cross_fade` 或
变换栈。**不引入动画框架，不自己写 `Glib::signal_timeout` 轮询。**

### 5. CSS 过渡用于控件级状态，不用于绘制

控件的悬停、选中、展开收起这类状态变化，优先在 `resources/style.css` 里写
`transition`，不要写进 C++。这是目前 0 处使用、成本最低的一块。

### 6. `GLArea` 暂不引入

shader 才是真正的表达上限，但代价是 GLSL、平台差异和一套独立的调试手段。**等出现
一个 `Snapshot` + Cairo 确实做不到的具体教学场景时再提 ADR**，不预先铺路。

### 7. 与 Blueprint 规则的关系

`AGENTS.md` 要求"能进 `.blp` 的都进 `.blp`"，`Snapshot` 视图属于其中列明的例外
第 3 条（"`.blp` 表达不了的绘制"）。自定义 widget 连同它必需的父容器可以留在代码里，
按规则在文件顶部注释写明为什么；它的**外壳、图例、说明面板仍然要进 `.blp`**。

## 落地顺序

按收益排，不求一次做完：

1. **值类别矩阵、类型推导图**（`type_semantics_lesson_page.cc` 的两个 `DrawingArea`）
   ——"切换两种写法看差异"是 ADR 0033 点名的互动，`push_cross_fade` 直接对应。
2. **知识点路线图**（同上第三个 `DrawingArea`）——点一个节点高亮它的先修链、其余
   降透明，现在只能整幅重画。
3. **`knowledge_graph_view` / `domain_graph_view`**——同样的聚焦需求，但边是贝塞尔
   曲线，迁移时**边仍然用 `append_cairo` 画**，只把层次与透明度交给 `Snapshot`。
4. **`chart_view`**——纯静态，除非要做数值变化的补间动画，否则不迁。

## 后果

- 自绘层出现两种写法并存：静态图 `DrawingArea` + `set_draw_func`，动态图自定义
  widget + `snapshot_vfunc`。这是按收益分的，不是历史遗留，评审时不要当成不一致去"统一"。
- 迁过去的视图从"每帧整幅重画"变成"节点树局部更新"，但**前提是把不变的部分拆成独立
  节点**；照搬原来的单块 `append_cairo` 得不到任何缓存收益。
- gtkmm 的 `Snapshot` 绑定比 C API 窄，写的时候要以 `gtkmm/snapshot.h` 为准，不要照抄
  C 文档里的渐变和路径节点。
- 不引入新依赖，Ubuntu 与 macOS 都走同一份代码，跨平台约束不变。
