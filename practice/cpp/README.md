# C++ 旧窗口

gtkmm / Meson 的 C++ 窗口，从课程应用拆出来单独放在这里（仓库 ADR 0141）。id 是 `cpp`，进程是 `athena-cpp`。

课程学习在 [`programming/c-plus-plus`](../../programming/c-plus-plus)（「C++ 教程」）。那边的侧栏可以启动本目录已经编好的程序。本应用不建掌握度，教学规范不生效。

```sh
launcher --root practice open cpp
python3 scripts/check.py cpp
```

本机已经编过的程序在 `build/athena-cpp`。目录从 `programming/c-plus-plus` 搬过来之后，`build/` 里记的还是旧路径；下次编译先 `meson setup build --reconfigure`。Windows 上这份程序链的是 MSYS2 mingw64 的 GTK，运行前要把 `C:\msys64\mingw64\bin` 放在 PATH 前面。
