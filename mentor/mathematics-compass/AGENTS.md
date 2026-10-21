# Athena 数学罗盘 — 项目协作规则

本文档是 **`mentor/mathematics-compass` 独立应用** 的项目级指令。仓库根 `AGENTS.md` 写各应用
共同遵守的规则；**改本应用时以本文为准**。

## 定位

- **图谱/参考类应用**（主仓库 ADR 0144、0174）：给数学学习指方向——五个数学学习应用的学习
  先后顺序、每站的学习目的、掌握要点与取舍。不教课、不判分、不建进度库、不建
  `content-contract.json`，跨应用教学规范对本应用不生效。
- **给唯一推荐路径**是本应用存在的理由（使用者 2026-10-21：先易后难、有所取舍）：每一步
  写明依据；被排后的内容注明什么情形再回来（`books.backtrack`）。只摆差异不下结论不是本
  应用的写法。推荐是编辑判断，依据写在正文里，不得包装成测量结果。
- 覆盖范围钉死在 ADR 0174 决策 2：路线节点是 `mathematics`、`selinger-linear-algebra`、
  `siefken-linear-algebra`、`octave-manual`、`sympy-tutorial` 五个；`math-tools` 只提及
  （companions），不占路线位。新增数学应用入圈时先进路线再做取舍，取舍变化连同提交说明。

## 内容纪律（本应用的核心约束）

唯一数据源是 `content/guide.json`，字段含义写在文件头的 `_` 里。

- **`updated` 是核对义务**：它是最后一次对照各数学应用内容现状核对的日期。数学应用的内容
  格局变化（新增章、换裁剪、覆盖推进、新应用入圈）时，本文件的对应描述要**随那次提交**
  一起更新并改 `updated`——导引描述的是当时的现状，静默过时等于撒谎。
- **不镜像教学内容**：导引只写「为什么学、掌握什么、舍什么」，不把其他应用的章节内容抄
  进来；内容以各应用为准，这里写岔了以学科正确语义与被引用应用为准。
- **缺口如实写明**（ADR 0129、0163）：高数应用不存在就是不存在（`gap` 节），不编造路线、
  不放占位章节；`scripts/check.py` 会拦 `TODO`/`待补`/`占位` 字样。
- **跨应用只走启动命令**：`launch` 字段只能是 `launcher open <id>`（校验强制），不引用别的
  应用的路径、配置或代码（ADR 0032）。
- 出处按参考类从简：节点的 `source` 写清教程/教材是什么、来自谁，不凭印象写（ADR 0043
  底线）；不判分内容不做出处门禁。

## 技术栈（本应用自有）

- **薄壳**：Tauri 2（Rust），只开窗口——导引内容在构建期由 Vite 打进前端，无自定义命令、
  无运行期内容读取、无进度库（模式与赛历同源，配置骨架最初复制自 `guide/sympy-tutorial`
  的 HEAD 版本、自带更新器插件；此后独立演进）。
- **界面**：Vite + React + TypeScript + Tailwind v4（渲染按摘星基线，ADR 0138；颜色走
  `src/styles.css` 令牌，深色随系统偏好）。
- 端口 1523（hmr 11523），进程 `athena-mathematics-compass`，`group` 为「数学」，
  更新器 endpoint `mathematics-compass.json`（ADR 0172）。

## 开发与验证

```sh
launcher open mathematics-compass
python3 scripts/check.py               # guide.json 结构 + id/端口对账 + 前端构建 + cargo check
```

只改了前端或内容时加 `--skip-rust`。图标改动后跑
`.cache/cargo-target/release/launcher icons` 重新生成位图（ADR 0065）。
