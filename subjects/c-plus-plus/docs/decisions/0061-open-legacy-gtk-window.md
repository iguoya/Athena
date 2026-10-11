# ADR 0061：新壳留一个入口，运行 practice/cpp 的编译成果

- 日期：2026-10-12
- 状态：已接受
- 依据：仓库 [ADR 0141](../../../../docs/decisions/0141-split-gtk-cpp-into-practice.md)

## 决策

1. **侧栏有「运行旧版窗口」。** 它只启动 `practice/cpp/build/` 里已经编好的 `athena-cpp`（以及还没按这个名字重编时留下的 `athena-c-plus-plus`）。路径写死，不接受调用方传入，也不提供任意命令。
2. **点击时不跑 Meson。** 程序不在，就告诉人到 `practice/cpp` 里执行 `meson setup build` 与 `meson compile -C build`。
3. **Windows 上把 `C:\msys64\mingw64\bin` 放到 PATH 前面再启动。** 本机这份已经编好的程序链的是 mingw64 的 GTK。
4. **`ATHENA_CPP_ROOT` 指向 `practice/cpp`。** 旧窗口不写本课程的 `progress/learning.db`。

## 后果

- 本应用的 `scripts/check.py` 不配置、不编译 Meson。
- 旧工程怎么构建、怎么单独打开，写在 `practice/cpp` 自己的 `app.json` 里。
