# practice/cpp 协作规则（C++ 旧窗口）

仓库级通用规则在 [`../../AGENTS.md`](../../AGENTS.md)，这里只写本项目自己的。

## 是什么

`practice/` 下的项目应用（仓库 ADR 0060、0141）：原来的 gtkmm C++ 窗口，从
`programming/c-plus-plus` 整棵拆出来。**不是学习应用**——课程、课表和
`progress/learning.db` 在「C++ 教程」。这里只把旧窗口编出来、跑起来。

id 是 `cpp`，进程 `athena-cpp`。不挂靠任何应用。不进仓库根的 pnpm / Cargo 工作区。

技术栈：C++20、GTK4 / gtkmm 4、Blueprint、Meson、GoogleTest。工程原文在 `docs/`。

## 规则

- 不引用 `programming/c-plus-plus` 的源码或课表。新教程如果要打开本窗口，只启动
  `build/` 里已经编好的程序（该应用 ADR 0061）。
- `ATHENA_CPP_ROOT` 指向本目录。不要把课程的进度库指到这里，也不要把这里的运行数据写进课程目录。
- Windows 上编译与运行走 MSYS2 mingw64：`PATH` 前置 `C:/msys64/mingw64/bin`，
  `PKG_CONFIG_PATH=C:/msys64/mingw64/lib/pkgconfig`。不要改用系统 PATH 里 Octave 自带的 gcc。
- 头文件、测试和 Meson 目标都在本目录。测试由 `scripts/check.py` 跑 Meson。

## 启动与验证

```sh
launcher --root practice open cpp
python3 scripts/check.py cpp
```
