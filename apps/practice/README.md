# 应用实践（尚未开工）

这个目录**还不是一个可运行的应用**：没有 `app.json`，启动器扫不到它；没有
`scripts/check.py`，仓库根的验证入口会跳过它。它现在的全部作用，是给从
`apps/cpp` 搬出来的「应用实践」内容存放代码，方便参考。

## 为什么从 apps/cpp 剥离出来

`apps/cpp` 首页原来是一张跨应用学科图谱，底下挂着两个本地分类：C++ 和
「应用实践」（`practice`，教的是数据结构与算法思想，不是 C++ 语言本身）。
首页图谱本身因为有了独立的 `launcher/` 而完成阶段性任务被移除
（apps/cpp ADR 0058），顺带也把「应用实践」这个跟 C++ 语言边界不重合的
分类一起搬了出来——`apps/cpp` 的边界一直是"教的是什么"，不是"用什么
语言写"，「应用实践」教的是数据结构与算法，不满足这条。

参照 `apps/dsa`、`apps/design-patterns` 先例——不满足边界的内容独立成
`apps/<id>/`，而不是留在原地降级凑合。

## 现在有什么

- [`pocket_cube/`](pocket_cube/)：C++ 演示和操作 2 阶魔方（顶点块、边块，
  只有 8 个角块）的状态表示与旋转。`state.{h,cc}` 是纯逻辑（立方体状态、
  旋转操作），`view.{h,cc}` 是 GTK4 `Gtk::Snapshot` 自绘渲染，
  `pocket_cube_page.{h,cc}` 是原来挂在 `apps/cpp` 学习页框架里的包装层，
  `pocket_cube.hpp` 是知识点入口。测试已经实现，**完整的打乱和求解算法
  还没做**。
- [`tests/`](tests/)：`pocket_cube_state_test.cc`、`pocket_cube_test.cc`、
  `pocket_cube_view_test.cc`，原样搬过来，没有接构建系统。
- [`practice_cube.blp`](practice_cube.blp)：原来的 GTK Blueprint 学习页
  界面定义。

## 将来开工时

技术栈按 2026-09-22 的讨论定了：跟 `apps/cpp` 同一套（GTK4/gtkmm、
Meson）——代码本来就是这个栈写的，不重写；Windows 上需要的 MSYS2 UCRT64
工具链发现已经在 `launcher/core` 里按应用 id 隔离过一次，接入时复用同一套
不用重新踩坑。

面板形态：不单独起一个独立进程，走 `launcher` 编排器同一套机制——
`launcher --root apps/practice list` 这种，只是把发现根目录从 `apps/*`
换成 `apps/practice/*`；每个小项目（PocketCube 是第一个）各自一份
`app.json`，跟仓库里其他应用同样的写法。启动器 GUI 里开一个独立的
「实践面板」分区，跟现有的学习应用面板区隔开——现有面板侧重知识学习，
实践面板侧重动手练习，两者背后共用同一套发现和启动逻辑，只是数据源和
界面分区不同。

开工时先把 PocketCube 接成一个真正的 `app.json`（`prepare`/`run` 照抄
`apps/cpp` 的 Meson 套路，缩小成只编这一个小项目），验证通过之后再考虑
是否要在 `apps/practice/` 下再加别的小项目——「应用实践」这个名字本来就
暗示以后会不止一个。
