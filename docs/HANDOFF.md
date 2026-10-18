# 交接清单：云会话做不到、需要人工或本地代理协助的事

规则见 [ADR 0164](decisions/0164-cloud-limits-handoff-and-content-thickness.md)。每条：**现状 → 为什么云里做不了 → 怎么做 → 验收**。
做完的条目不删，把 `[ ]` 改成 `[x]` 并写上提交。**本地代理接手前先读本文件与对应应用的 `AGENTS.md`。**

云会话的限制（2026-10）：出口代理只放行 GitHub（克隆）与少数包源（PyPI、npm、apt）；视频站、GeoGebra 官网与 wiki、
Octave 文档站、大学站点 PDF 一律拒绝；没有显示设备；不能打开 Tauri 窗口；没有 macOS、Windows 构建环境；磁盘配额约几 GB。

## 一、拿不到的教材（需要人工给文件，或本地代理联网取）

- [ ] **Lachniet《Introduction to GNU Octave: A brief tutorial for linear algebra and calculus students》**（CC BY-SA 4.0，约百页，
  专为线代与微积分学生写的 Octave 入门小册，口碑最好，是 Octave 的首选教材）
  - 现状：没有入库。`guide/octave-manual` 用的是官方参考手册（裁剪），不是教程。
  - 为什么：只有大学站点（wcc.vccs.edu）与 Marshall 等库里的 PDF，没有 GitHub 源，云里下不了。
  - 怎么做：人工下载 PDF 放进新应用 `guide/octave-tutorial/upstream/`（gitignore）；PDF 没有结构化源码，按页精读：
    `pdftotext -layout` 抽文字，按章节切成段落快照（沿用 `guide/octave-manual` 的快照格式与 `scripts/tr.py`），练习由 Octave 复算。
    新应用走 `new-app` skill 的流程，id 建议 `octave-tutorial`，端口取 1521 起的下一个空号，先写应用级 ADR。
  - 验收：`python3 scripts/check.py octave-tutorial` 通过；页面能打开；题答案经 Octave 复算。
- [ ] **GeoGebra 官方手册**（wiki.geogebra.org/en/Manual）
  - 现状：没有任何 GeoGebra 应用。GitHub 上没有以 GeoGebra 为主的开源书，`geogebra/geogebra` 仓库只有软件源码。
  - 为什么：手册在 MediaWiki 站点上，云里连不上；站点许可需要确认。
  - 怎么做：有网的本地代理用 MediaWiki 导出（`Special:Export` 或 `api.php?action=query&export`）取手册命令与工具两部分的 XML，
    解析成块流后接 `guide/octave-manual` 的快照管线；GeoGebra 的习题要「做出一个构造再核对数值」，核对点用 GeoGebra 的命令行或
    `geogebra-cas` 复算。先问使用者要不要做，再起应用 `guide/geogebra-manual`。
  - 验收：同上。
- [ ] **视频课（B 站、YouTube 等）**
  - 现状：一门视频课都没建。规则是：一门视频课一个应用，只有字幕或讲稿文本拿得到才建，内容为字幕文本加原视频外链，
    不嵌播放器、不放视频。
  - 为什么：视频站云里连不上。
  - 怎么做：本地代理用 `yt-dlp --write-subs --skip-download <url>`（YouTube）或 `BBDown`/`you-get`（B 站）取字幕，
    转成段落快照，按「段落 + 时间戳 + 外链」入库；练习自编并可机器核对。
  - 候选（使用者指定或确认后再做）：3Blue1Brown「线性代数的本质」「微积分的本质」——**字幕在 GitHub 仓库 `3b1b/captions`，
    云里能取**，只缺使用者点头（它讲直观化的数学，不是工具）；其余 B 站课程等使用者给出具体链接。

## 二、候选教材（数学工具多本好书，一本一个应用，云里能取的会继续做）

按「GitHub 上有源码、口碑好、与线代或高数相关」排序，来源与取得方式如下，**尚未开始**：

- [ ] **SciPy Lecture Notes**（`scipy-lectures/scipy-lecture-notes`，CC BY 4.0）：NumPy、Matplotlib、SciPy、SymPy 的体系化讲义，
  讲数值线代、积分、微分方程、绘图，图由代码生成。云里能取（GitHub），建议下一本，id `scipy-lecture-notes`，按基础/进阶分层。
- [ ] **Computational Mathematics with SageMath**（Zimmermann 等，GitHub 有源，CC BY-SA）：把 SymPy 之外的符号计算与线代、微积分合在一起讲。
- [ ] **Linear Algebra with SageMath**（`SageMathOER-CCC/linear-algebra-with-sage`，PreTeXt）与 **Understanding Linear Algebra**
  （David Austin，`OpenMathBooks/linear-algebra-companion`，PreTeXt）：把工具嵌进线代教材。
- [ ] **Matplotlib 官方教程**（`matplotlib/matplotlib` 仓库 `galleries/tutorials`）与 **NumPy 官方入门**（`numpy/numpy` 仓库 `doc/source/user`）：
  图形化表现力最强的两个通用工具。

## 三、需要真实桌面或本地环境才能做完的事

- [ ] **Octave 插图改用 Octave 原生渲染**
  - 现状：`guide/octave-manual/content/figures/*.svg`（7 幅）由 `scripts/render_figures.py` 生成：数据由真 Octave 算出，
    图形由 matplotlib 重绘（风格近似 Octave，不是逐像素一致）。
  - 为什么：云里的 Octave 8.4 在无显示时创建坐标轴就失败（`ft_text_renderer: invalid bounding box`，换字体、装 Xvfb 都没解决）。
  - 怎么做：在有图形能力的机器上装 Octave 8.4，对每幅图运行 `upstream/octave/doc/interpreter/plotimages.m`
    （`plotimages("<输出目录>", "<图名>", "svg")`，图名见 `content/scope.json` 的 `figures` 与 `figures_more`；`interp*` 用 `interpimages.m`），
    把产出的 SVG 放进 `content/figures/` 覆盖同名文件。SVG 里的 id 要加图名前缀（避免同页多图冲突，参考 `guide/selinger-linear-algebra/scripts/render_figures.py` 的 `namespace_ids`）。
  - 验收：`python3 scripts/check.py octave-manual` 通过；`launcher open octave-manual` 的绘图页里图正常显示。
- [ ] **真实 Tauri 窗口里打开四个新应用**：`launcher open selinger-linear-algebra`、`siefken-linear-algebra`、`sympy-tutorial`、`octave-manual`。
  云里只验证了：`cargo check`、网页预览（Chromium 截图）、`scripts/check.py`。作答写入进度库（`learning.db`）、窗口行为、图标都没在真机上看过。
- [ ] **macOS 与 Windows 构建**：优先级 macOS ≈ Windows > Linux（ADR 0051）。`pnpm install` 后 `pnpm run tauri:dev` 在两个平台各跑一遍。
  特别注意（已踩过的坑）：大小写不敏感文件系统上的同名文件——已把 `inline.ts` 改名 `splitInline.ts`，仍请抽查别的应用。
- [ ] **进度同步**：启动器的同步代理把四个新应用的 `attempts` 表推到路由器 PG，没有端到端验证过（云里没有路由器）。
- [ ] **CI 与工作流检查**：`python3 scripts/check.py --sources-only` 在云里因缺 `actionlint`、`shellcheck` 而退出码为 1（与本次改动无关）；
  `gh workflow run ci.yml` 没有触发过。本地装好这两个工具后重跑。
- [ ] **Octave 复算需要 Octave**：`guide/octave-manual` 的 `check.py` 在装有 Octave 的机器上才复算练习答案，否则只报告跳过；
  CI 机器若要复算，需要先装 Octave 8.4。

## 四、人工校对

- [ ] **译文校对**：四个新应用的中文译文均为机器翻译（并行译员逐段写，公式与代码逐条校验一致，但语义与术语没有人工通读）。
  建议抽读每个应用的几页，把改动直接写进 `content/sections/*.json` 的 `zh`（`tr.py` 导入不会覆盖已译单元，直接改 JSON，再跑 `check.py`）。
- [ ] **练习的口味**：「试一试」与核对点是自编的；难度、题量、误区选项是否贴合你的学习节奏，需要你试做后反馈。
- [ ] **上游笔误**（照原文入库、没有改，核对点避开了这些题）：
  - Selinger：`GaussianElimination` 习题 4 解答有误；`Matrices-Transpose`、`Matrices-Projections` 解答有笔误；
    `Determinants-Application-Inverse` 习题 5（逆矩阵与行列式符号错）；`Eigenvalues-Geometric` 习题 4（特征向量与特征值配反）；
    `InnerProductSpaces-OrthogonalMaps` 习题 2（矩阵系数印错）；`InnerProductSpaces-Application-QuadraticForms` 习题 4（u² 系数应为 1）。
  - Siefken：`appendix1` 习题 4(3)（b 的第二分量 14 与 12 不一致）；`appendix2` 习题 2（解答条目与小题对不上）；
    `appendix3` 习题 6(1) 解答矩阵字母错位、6(3) 题干 Y 的 (1,2) 元素应为 −a、7(3) 解答「a=b」应为「a=0 或 b=0」。
  - SymPy 教程：`printing` 里 `init_session()` 示例输出写的是 1.13.0；`intro` 与 `basic_operations` 里两处浮点输出是 Python 2 年代的位数
    （已登记在 `verify_examples.py` 的 `KNOWN_STALE`）。
  - Octave 手册：`isvector` 说明被上游截断（`<` 之后的内容丢失）；多处函数说明有半截句（`eye`、`quad` 等）；`quadgk` 简介写成 Gauss-Konrod。

## 五、工程基线收尾（ADR 0170，云会话做不到的部分）

- [ ] **Actions 钉提交 SHA**
  - 现状：`ci.yml`、`release.yml`、`pages.yml` 里的第三方 action 都只钉了标签（`actions/checkout@v7`、`tauri-apps/tauri-action@v0` 等），标签可被改写，发版任务又带写权限。
  - 为什么：要读各 action 仓库里标签对应的提交，云会话只能访问本仓库。
  - 怎么做：本地装 `pinact`（`pinact run`）或 `ratchet`，一次把标签换成「提交 SHA + 版本注释」；`dependabot.yml` 已有 `github-actions` 生态，会继续按月维护 SHA。
  - 验收：`python3 scripts/check.py --sources-only` 通过（actionlint）；`gh workflow run ci.yml -f app=sources` 通过。
- [ ] **主分支保护与仓库安全开关**（GitHub 仓库设置，不在代码里）
  - 怎么做：Settings → Branches：对 `main` 打开「禁止强推、禁止删除」（单人直推可保留，不必强制 PR）；Settings → Code security：打开 Secret scanning、Push protection、Dependabot alerts。
  - 为什么要做：本地 `main` 与远端 `main` 曾出现各 50 个提交的分叉，说明远端被强制更新过；Push protection 能在密钥进历史之前拦下。
- [ ] **首次 CI 上跑 `--security`，确认 cargo-deny**
  - 现状：云里连不上 RustSec 公告库，只验证了 `deny.toml` 能被解析；gitleaks 与 `pnpm audit` 已在云里跑通。
  - 怎么做：`gh workflow run ci.yml -f app=sources`，看「Security scan」步骤里 cargo-deny 两个工作区的输出。若只有我们治不了的公告（如 gtk3 绑定停止维护），把它们写进 `deny.toml` 的 `ignore` 并注明理由，再考虑把 cargo-deny 升级为阻断。
- [ ] **两处真实依赖公告**（pnpm audit 首扫发现，按风险排期，不借工程基线盲升）
  - `maplibre-gl`（`mentor/jiuzhou`）：5.24.0，公告要求 ≥ 6.4.1，跨大版本，需在真机上验证九州地图渲染。
  - `katex`（`certification/embedded`）：0.16.47，低危，公告要求 ≥ 0.18.2。
- [ ] **rustfmt 全仓库格式化后，Tauri 矩阵确认编译通过**：排版不改语义，但 Tauri 壳依赖 GTK/webkit，云里只编过 `launcher-core`。下一次手动 CI 全量跑时留意。

## 六、已知的取舍（不是缺陷，记在这里免得再问）

- Octave 手册是参考手册，按「基础/进阶」分层、默认只显示基础（见 ADR 0164 决策 2）；SymPy 教程本身就薄，不分层。
- 两本线代教材按使用者要求精读全书，不分层。
- 上游图（Selinger、Siefken 的 TikZ 图）已移植为 SVG；Octave 插图见上文「改用原生渲染」。
