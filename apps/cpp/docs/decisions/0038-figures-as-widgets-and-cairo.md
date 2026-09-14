# ADR 0038：插图改由 GTK 控件与 Cairo 自绘承载，退出 SVG 图片路线

- 日期：2026-09-12
- 状态：已接受；`cpp.TypeSemantics` 先行改造，后续章节按本 ADR 的判据选载体
- 延续：ADR 0024（内容由 GTK 控件承载）、ADR 0033（能算出来的画成活的）、
  ADR 0035（把 GTK 的表达上限用满）
- 不修订：技术栈边界——本 ADR **不引入新依赖**，恰恰是为了去掉一个

## 背景

学习页的插图此前是静态 SVG：`.blp` 里声明 `Gtk::Picture`，页面代码
`set_resource("/app/articles/cpp/images/xxx.svg")`，文件打进 GResource。
2026-09-12 这条链路暴露了三个问题。

**一、它会静默失效。** 开发机上 Homebrew 重装 librsvg 后没有 link，
`libpixbufloader_svg.so` 不在 gdk-pixbuf 的 loaders 目录里，而 `loaders.cache`
仍记着它。结果是**每一张插图都显示为空白，且 GTK 不报任何错**——界面上看起来
只是"图没写"，排查要一路查到 pixbuf loader。图片是外部解码器负责的资源，它的
失败不在我们的编译期，也不在我们的类型系统里。

**二、载体选错了。** 盘点当时的八张图，其中三张（四种初始化写法、enum class
的三道边界、五种转换的检查层）本质是**表格**：若干行文字加一个底色标记。把
表格做成图片，等于放弃字体跟随系统字号、放弃主题适配、放弃文字选中与搜索、
放弃无障碍朗读，还让"改一句措辞"变成"重画一张图"。

**三、它和正文会漂移。** ADR 0034 删掉 Markdown 手册时，五张为手册画的图留在
`resources/articles/` 下无人引用，配色和字号也不再符合现行规范。图片是不参与
校验的资产，正文改了它不会跟着改，删了内容它也不会消失。

## 决策

插图不再用 SVG 图片承载，按**内容里有没有几何关系**分两种载体：

| 内容形态 | 载体 | 依据 |
|---|---|---|
| 表格、并排对照、卡片清单、带标记的条目 | `.blp` 控件树 | 文字仍是文字：可选中、可搜索、跟随系统字号与主题、无障碍可读，改措辞不必重画 |
| 连线、箭头、时间轴、层次布局、坐标、动画，以及位置由运行时数据算出来的结构 | `Gtk::DrawingArea` / `Gtk::Snapshot` 自绘 | `.blp` 表达不了这些；ADR 0035 已经把自绘定为这类内容的正路 |

一张图同时包含两者时，文字部分用控件、几何部分用自绘，不为了统一而把文字也
画进画布。

**不 vendor SVG 渲染库。** 曾考虑把 librsvg 或 lunasvg 收进仓库：前者核心是
Rust 并依赖 cairo/pango/harfbuzz/gdk-pixbuf，等于引入一条新的构建链；后者是
可行的纯 C++ 方案，但它解决的是"SVG 怎么解码"，而上面三个问题里只有第一个
与解码有关。载体选错和内容漂移换一个解码器并不会消失。

## 范围：项目不再依赖任何 SVG 渲染

插图之外，运行时还有两处曾经要解码 SVG，一并处理了：

- `resources/backdrop.svg`（页面底纹，经 GTK CSS 的 `url()` 加载）改写成
  GTK CSS 的多层渐变，由 GSK 直接画，零文件；
- 应用图标改为提交 PNG 尺寸集（`resources/icons/<size>x<size>/apps/`）。
  macOS 打包直接用这些 PNG 拼 `.iconset` 交给 `iconutil`，不再需要
  `rsvg-convert`；Linux 侧装的是 hicolor 的 PNG 尺寸目录。

界面上仍有大量 GTK 自带的 symbolic 图标，那些不是我们的文件：GTK 4.20 起
内建了一个覆盖 99% Adwaita symbolic 图标的 SVG 解析器，走的是图标路径而不是
`GdkTexture`，因此不依赖 librsvg。个别 legacy 图标它解析不了（例如
`utilities-terminal-symbolic` 的 `path` 上带 `font-weight`），选图标时避开
即可——本次就换掉了一个。

**这条内建路径是留着的。** 被否掉的不是 SVG 本身，而是"把 SVG 交给
`Gtk::Picture` / `Gdk::Texture`"——那里只内建 PNG/JPEG/TIFF，SVG 必然回退到
外部 loader。确有 SVG 更合适的场合（图形复杂、由设计工具产出、不需要跟随
字号与主题），可以把它作为图标资源挂进 icon theme
（`Gtk::IconTheme::add_resource_path()` + `icon-name`），由 GTK 内建解析器
渲染，不引入 librsvg；代价是要求 GTK ≥ 4.20，并受图标路径的尺寸与着色语义
约束。选择顺序是：能用控件就用控件，需要几何就用 Cairo，两者都不合适再考虑
这条内建 SVG 路径。生成器的校验按这个顺序写：它拦的是解码器依赖那条路，
不是仓库里存在 `.svg` 文件。

验证方式是把 gdk-pixbuf 的 SVG loader 从 `loaders.cache` 里摘掉再跑一遍应用：
改造完成后启动零报错。`scripts/package_macos.py` 也相应放宽——cache 里记着
而文件不在的 loader 整块跳过，不再让打包失败。

## 后果

**得到**：插图里的文字重新变成文字——跟随系统字号（`ui-default-font-size` 的
15pt 下限对它们同样生效）、跟随主题、可选中可搜索、无障碍可读；插图参与
`.blp` 与 CSS 的统一样式，不再各自维护一套配色；表格类内容改措辞只改 `.blp`；
插图不再依赖外部解码器，缺环境时是编译错误而不是一块空白。

**付出**：几何类插图要写 Cairo 代码，比改一段 SVG 慢；两种载体意味着写内容前
要先判断该用哪种，判据就是上表；已有的八张 SVG 需要逐张改造，期间新旧两种
载体会并存一段时间。

**连带**：`scripts/generate_project.py check` 里的插图校验换了内容——从"引用的
图必须存在"变成"`resources/` 下不允许再出现 SVG、不允许引用已废弃的插图目录"，
`.blp` 的 `Picture` 必须有人填资源这条保留（PNG 同样适用）；`tests/` 里为 SVG
解码守门的两个测试随之退场。`resources/articles/` 不再存放教学插图。
