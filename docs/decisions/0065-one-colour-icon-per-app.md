# ADR 0065：每个应用一份彩色图标，启动器、任务栏、应用界面三处同源

- 日期：2026-09-28
- 状态：已接受
- 影响：各应用的 `icon.svg` 含义改变、`app.json` 的 `icon` 块新增 `renders`；
  编排器新增 `launcher icons`；启动器图块不再用图标表达运行态；启动器自己的标志
  换成同画风虎头
- 关系：落实 [ENGINEERING.md](../ENGINEERING.md)「能在构建期解决的不要留到运行期」；
  不改 [ADR 0046](0046-unified-dev-orchestrator.md)「新增应用启动器不改代码」

## 背景

到 2026-09-28，同一个应用在不同地方长得不一样，彼此之间也不像一家：

| 应用 | 启动器图块 | 任务栏 / 标题栏 | 应用自己的界面 |
|---|---|---|---|
| dsa / english / mathematics | accent 底 + 白字形 | Tauri 默认标志，三个一模一样 | 无标志（english 是文字块「E2」） |
| driver | 同上（字形还是「手机」） | Flutter 默认标志 | 无 |
| cpp | 同上 | exe 资源里是 C++ 六边形；GTK 图标主题里是**启动器的虎头** | 关于对话框里是虎头 |
| c / polaris | 同上 | 直接拿白字形 SVG 当窗口图标，浅色任务栏上**几乎看不见** | 无 |
| pocket-cube | 同上 | 没设，GTK 默认 | 无 |

根子在于 `icon.svg` 被定义成「白色字形，配 `accent` 底色显示」：它自己不是一个完整
图标，只有启动器知道要垫底色，别处直接拿来用就是白纸上的白字。另外启动器图块运行时
加光环、放大、换投影，同一个应用在列表里有两副面孔。

## 决策

1. **`icon.svg` 就是这个应用的图标本身**：透明底、自带颜色、不需要谁再垫底色。
   启动器图块、窗口/任务栏/Dock、应用自己界面上的标志，三处都从这一份来，不另画。
2. **每个应用按自己的身份概念挑本领域最贴切、最好看的图标，不强求彼此画风一致。**
   做法是在开放许可的图标库里按概念检索（Iconify 汇集的 Fluent、Streamline、
   SVG Logos 等彩色集），逐个比较 16–256px 的实际效果再定，不拿「最接近的现成
   emoji」凑数：

   | 应用 | 身份概念 | 图标 |
   |---|---|---|
   | c / cpp | 语言本身 | 官方标志（SVG Logos，CC0） |
   | dsa | 节点构成的树 | Fluent Color「Org」：一根带两子，就是二叉树（MIT） |
   | mathematics | 用线性变换讲线性代数 | Streamline「Transform Right」：正方形被变成平行四边形（CC BY 4.0） |
   | driver | 科目一、四考交通法规 | Fluent Emoji 红绿灯（MIT） |
   | english | 拉丁字母 | Fluent Emoji「abc」（MIT） |
   | polaris | 北极星本身 | Fluent Emoji 发光的星（MIT） |
   | pocket-cube | 2 阶魔方 | 自己画：库里的魔方全是 3 阶，用了反而说错 |
   | 启动器 | Athena 虎头标志 | Fluent Emoji 虎头（MIT） |

   深色任务栏上看不见的（近黑描边）要改色，改动写进注释。出处、许可与改动写在每个
   `icon.svg` 顶部；CC BY 的署名靠这段注释随文件走。

   （同日修订：初稿写的是「画风统一取 Fluent Emoji」，使用者看过效果后改为按概念
   逐个挑选、不要求协调。）
3. **位图由 `launcher icons` 生成并提交，应用构建不依赖启动器。** 每个应用在
   `app.json` 的 `icon.renders` 里声明要哪些派生文件（相对应用目录的路径 → 边长，
   或 `"ico"` / `"icns"`），编排器照单渲染。理由：
   - Fluent 的 SVG 大量用滤镜（`feGaussianBlur`），Qt SVG、GTK、flutter_svg 要么
     不支持要么各画各的；resvg 画得对，启动器本来就依赖它。
   - 平台图标格式（`.ico`、`.icns`、Tauri 的一组 PNG、GTK 图标主题）本来就是位图，
     是构建期的事，不该留到运行期各自去渲染 SVG。
   - 产物是应用自己目录里的普通文件，应用照常独立构建，不引用启动器的任何路径
     （ADR 0032「构建完全隔离」不破）。改了 `icon.svg` 就重跑一次；
     `launcher icons --check` 只核对不写，产物过期时退出码非零。
4. **图标不表达运行状态。** 启动器图块在运行、启动中、未运行三种状态下是同一张
   图、同样大小、同样投影；状态只由图块下方的状态点表达（绿 / 橙 / 灰）。
5. **任务栏上每个应用恰好一个按钮、一个自己的标志。** 窗口图标和可执行文件资源里的
   图标用同一份派生文件：Qt 应用两处都设；GTK4 在 Windows 上只认 exe 资源（它删掉了
   逐窗口设图标的 API），所以 GTK 应用必须把 `.ico` 编进 exe；Tauri、Flutter 用各自
   框架的图标位。任何应用都不得借用启动器的虎头或另一个应用的图标。
6. **`accent`、`letter`、`symbol` 保留**，作为没有 `icon.svg` 的新应用的兜底：
   启动器仍会用 `accent` 底色加 `letter` 画一块。新增应用照旧只放 `app.json` 与
   `icon.svg`，启动器不改代码。

## 后果

- 换一个应用的图标：改它的 `icon.svg`，跑 `launcher icons`，提交 SVG 与派生文件。
- 派生 PNG / ICO 进版本库，体积每个应用几十到几百 KB，换来的是任何人 clone 下来
  不装额外工具就能构建出带正确图标的应用。
- Linux 下 Flutter 的窗口图标、各应用的 `.desktop` 注册仍按各自现状，不在本 ADR
  范围内（ADR 0051：Linux 如实降级）。
