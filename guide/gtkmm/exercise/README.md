# exercise/ — 官方示例代码（原样镜像）

`<示例集>/<示例>/` 是官方仓库 `gtkmm-documentation` 中 `examples/book/` 的
**逐字镜像**（版本与 commit 由 `upstream.json` 钉住），代码、注释、许可头
一个字不改；许可随文件头（GPL-2.0-or-later）。

- 构建脚本集中在 `CMakeLists.txt`，产物落 `build-exercise/`；与上游对照：
  `git diff --no-index exercise/buttons upstream/gtkmm-documentation/examples/book/buttons`
- **禁止就地修改**：要改的地方属于上游；教学改造（加协议、拆 TODO）在 `demos/`。
- 课程壳在教程节页提供「编译并运行」与源码查看；清单见
  `content/demos.json` 的 `examples` 数组（应用 ADR 0006）。

## 目录

| 目录 | 教程锚定 |
|---|---|
| `buttons/button` | 第 6 章「普通按钮」Example（正文链接） |
| `buttons/togglebutton` | 第 6 章「开关按钮」（官方目录有、正文未单独链接） |
| `buttons/checkbutton` | 第 6 章「勾选按钮」Example（正文链接） |
| `buttons/radiobutton` | 第 6 章「单选按钮」Example（正文链接） |
| `buttons/scalebutton` | 章级：官方示例集附带，正文未提 |
