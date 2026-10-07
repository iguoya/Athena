# Athena Math Tools — 项目协作规则

本文档是 **`subjects/math-tools` 独立应用** 的项目级指令,不依赖其他应用即可完成开发与
运行。仓库根 `AGENTS.md` 写各应用共同遵守的规则;改本应用时以本文为准。

## 定位

- **数学学习的配套工具**(ADR 0084,原在 `practice/`):做能跑的数学工具,不追求知识点覆盖,**不建进度库**,
  跨应用教学规范不生效。
- 当前包含:练习纲要(七章二十四条的练习本,勾选打卡)、矩阵实验室(行列式/逆/
  转置/特征值/幂)、函数绘图(表达式绘制、拖拽平移、滚轮缩放)。
- **练习纲要只是清单,不是教学系统**:勾选状态存 localStorage
  (`mt-curriculum-done`),是个人打卡便利,不是掌握度记录;纲要数据在
  `src/data/curriculum.ts`,只写「练什么、验收什么」,不写讲解正文。若将来要升级成带讲解与掌握度的学习应用,那是应用类型的变化(它现在归图谱/参考类,
  ADR 0084),先立 ADR 再动。

## 技术栈与选型理由

- **Tauri 2**(Rust 壳 + 系统 WebView):界面是 Web 技术;若将来要嵌 GeoGebra 等只有
  Web 运行时的组件,同壳零摩擦;仓库内 `subjects/ascent`、`subjects/mathematics` 已
  有 Tauri 2 前例,配置与坑均有参照。
- **Vue 3 + TypeScript + Vite**:单文件组件把模板、样式、逻辑就近内聚,适合按块渲染
  的工具界面;`<Transition>` 内置,基础转场不依赖库。
- **Tailwind CSS 4**:原子化样式,经 `@tailwindcss/vite` 插件接入;主题令牌集中在
  `src/style.css` 的 `@theme`。
- **motion-v**:motion 的 Vue 版,负责入场编排、spring 与 layout 动画;基础转场优先用
  Vue 内置 `<Transition>`,motion-v 只做 CSS 表达不了的部分。
- **lucide-vue-next** 图标;**mathjs** 做矩阵运算与表达式求值,不自己写数值内核。
- 字体:Sora(标题/拉丁)、Noto Sans SC(正文中文)、JetBrains Mono(数字/公式),
  经 `@fontsource` 打进包内,离线可用。
- 包管理用 **npm**(本机 corepack 无权限写 Program Files,不引入 pnpm 依赖)。

## 命名与端口

- id `math-tools`,进程/二进制 `athena-math-tools`;dev 端口 **1451**(strictPort,
  避开 ascent 的 1440)。
- 窗口标题「数学工具」;应用内文案用中文。

## 开发与运行

- 打开应用走启动器:`launcher open math-tools`(ADR 0044、0046)。
- 手动开发:`npm install` 后 `npm run tauri:dev`(改前端即时热更);
  仅看界面可 `npm run dev` 后浏览器开 http://localhost:1451 。
- 打包:`npm run tauri:build`(打包前需先补 `src-tauri/icons/`,当前
  `bundle.active: false`)。

## 验证

- `python3 scripts/check.py`:app.json 合法性 + `vue-tsc` 类型检查 + `vite build`;
  缺 `node_modules` 时先按 lock `npm ci`,不跳过。
- 根目录 `python3 scripts/check.py math-tools` 透传到本脚本。

## 约定

- 影响本应用架构边界的新决定,在 `docs/decisions/` 增补 ADR 后再动代码。
- **皮肤机制**(与拾阶 skins 同构):一套组件、令牌换氛围。三套皮肤(晴空/晨读/草稿)
  **均为浅色系**(应用不使用暗色),定义在 `src/style.css` 的 `--tk-*` 令牌块,清单与
  切换在 `src/theme.ts`。组件里**不硬编码主色**——渐变/发光/主色文字用
  `accent-gradient`、`accent-glow`、`accent-fg`、`accent-soft`、`text-gradient`、
  `tk-display` 这些 utility;工具卡片的品类色(紫/青/橙)是功能识别色,不随皮肤变。
  新增皮肤 = 加一段 `--tk-*` 令牌 + `SKINS` 一行,不动组件;若将来要加暗皮肤,
  需令牌块配 `html.dark`(组件的 `dark:` 变体仍在,属新增决定)。
- 练习勾选(`mt-curriculum-done`)与皮肤(`mt-skin`)都存 localStorage,是本机
  便利,不进版本库。
