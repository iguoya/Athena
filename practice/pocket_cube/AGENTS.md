# practice/pocket_cube 协作规则（PocketCube 2 阶魔方）

仓库级通用规则在 [`../../AGENTS.md`](../../AGENTS.md)，这里只写本项目自己的。

## 是什么

`practice/` 下的项目应用（ADR 0060）：做出一个能跑的东西，**不是学习应用**——不追求
知识点覆盖、不建进度库，「跨应用教学规范」对它不生效。

**现状**：2 阶魔方（8 个角块）的状态表示、旋转和展开图已经实现；**打乱与求解算法还没做**。
不要把后者当成已有功能。

技术栈：C++20、GTK4 / gtkmm 4、Blueprint、Meson、GoogleTest。

## 规则

- **头文件相对 `practice/` 解析**：写 `#include "pocket_cube/state.h"`，不写
  `"state.h"`。留这层前缀，是为了 `practice/` 下以后再加小项目时同名头文件不冲突。
- **测试在 `practice/tests/`**，由本目录的 `meson.build` 引用。纯逻辑（`state`、
  `pocket_cube`）的测试不依赖 GTK，渲染（`view`）单独一个测试可执行文件。
- **不引用别的应用的文件。** `compat/glib_final_type_shim.h` 是从 `subjects/cpp` 复制
  来的同一份垫片，因为应用之间不互相 include（根 `AGENTS.md`「独立应用」）。上游
  MSYS2 的 glibmm 跟上后两边都可以删。

## 启动与验证

```sh
launcher --root practice open pocket-cube   # app.json 的 id 是 pocket-cube
python3 scripts/check.py pocket_cube        # 仓库根执行：Meson 配置、构建、测试
```
