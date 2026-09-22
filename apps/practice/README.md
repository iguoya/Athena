# 应用实践

跟 `apps/dsa`、`apps/c` 这些学习应用不是一回事：这里放的是"动手做一个小
东西练手"，不追求知识点覆盖、不接掌握度体系。目录下每个子目录是一个独立
的小项目，各自一份 `app.json`——`apps/practice` 本身**不是**一个应用，
没有自己的 `app.json`，跟仓库根验证入口不打交道，是"应用实践"这个概念的
容器，不是某个具体程序。

## 为什么会有这个目录

`apps/cpp` 首页原来是一张跨应用学科图谱，底下挂着两个本地分类：C++ 和
「应用实践」（`practice`，教的是数据结构与算法思想，不是 C++ 语言本身）。
首页图谱本身因为有了独立的 `launcher/` 而完成阶段性任务被移除
（apps/cpp ADR 0058），顺带也把「应用实践」这个跟 C++ 语言边界不重合的
分类一起搬了出来——`apps/cpp` 的边界一直是"教的是什么"，不是"用什么
语言写"，「应用实践」教的是数据结构与算法，不满足这条。参照 `apps/dsa`、
`apps/design-patterns` 先例——不满足边界的内容独立成 `apps/<id>/`，而
不是留在原地降级凑合。

## 现在有什么

- [`pocket_cube/`](pocket_cube/)：**已经是一个能跑的独立应用**（2026-09-22
  接上 `app.json`）。C++ 演示和操作 2 阶魔方（顶点块、边块，只有 8 个角块）
  的状态表示与旋转，测试已经实现，**完整的打乱和求解算法还没做**。技术栈
  跟 `apps/cpp` 同一套（GTK4/gtkmm、Meson）——代码本来就是这个栈写的，
  不重写。`state.{h,cc}` 是纯逻辑，`view.{h,cc}` 是 `Gtk::Snapshot` 自绘
  渲染，`main.cc` 是独立窗口入口（不再依赖 `apps/cpp` 的 ChapterMeta/
  ContentLoader/Builder 页面框架），`pocket_cube_page.{h,cc}` 是原来挂在
  `apps/cpp` 学习页框架里的旧包装层，保留作参考，不再被构建引用。

  ```sh
  cd apps/practice/pocket_cube
  meson setup build && meson compile -C build
  # 或者从仓库根用编排器：
  launcher --root apps/practice open pocket-cube
  ```

- [`tests/`](tests/)：`pocket_cube_state_test.cc`、`pocket_cube_test.cc`、
  `pocket_cube_view_test.cc`，原样搬过来，**还没有接进 `pocket_cube/
  meson.build`**——下一步要做的事之一。

## 发现与启动

不单独起一个独立进程，走 `launcher` 编排器同一套机制——发现根目录从
`apps/*` 换成 `apps/practice/*`（`launcher/core` 的 `discover_in()` 通用
版本），每个小项目各自一份 `app.json`，跟仓库里其他应用同样的写法。

**还没做**：启动器 GUI（`launcher/gui`）里的独立"实践面板"分区，跟现有
学习应用面板区隔开——现有面板侧重知识学习，实践面板侧重动手练习，两者
背后共用同一套发现和启动逻辑，只是数据源和界面分区不同。现在只能通过
终端 `launcher --root apps/practice open <id>` 或直接进子目录手动构建。

## 加新的小项目

在 `apps/practice/` 下建一个新子目录，照 `pocket_cube/app.json` 的样子
写一份自己的 `app.json`，`launcher --root apps/practice list` 就能发现
它——不需要改 `launcher` 的任何代码。「应用实践」这个名字本来就暗示以后
会不止一个。
