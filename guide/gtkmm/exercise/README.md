# exercise/ — 官方示例代码（原样镜像）

`<示例集>/<示例>/` 是官方仓库 `gtkmm-documentation` 中 `examples/book/` 的
**逐字镜像**（版本与 commit 由 `upstream.json` 钉住），代码、注释、许可头
一个字不改；许可随文件头（GPL-2.0-or-later）。

- 构建脚本集中在 `CMakeLists.txt`（每示例的源文件清单取自上游 meson.build），
  产物落 `build-exercise/`；与上游对照：
  `git diff --no-index exercise/<示例集> upstream/gtkmm-documentation/examples/book/<示例集>`
- **禁止就地修改**：要改的地方属于上游；教学改造（加协议、拆 TODO）在 `demos/`。
- 课程壳在教程节页提供「编译并运行 / 打开工作区 / 查看源码」；清单见
  `content/demos.json` 的 `examples` 数组（应用 ADR 0006、0009）。
- 已导入教程第 6–17 章（第 16 章 Adjustments 官方无示例目录，正文代码已由
  ADR 0007 内嵌进快照）；`treeview/custom_treemodel` 是 32 位时代代码，
  构建端放宽 `-fpermissive`，代码原样。
