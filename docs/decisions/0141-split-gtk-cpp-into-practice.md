# ADR 0141：旧版 gtkmm 窗口独立为 practice/cpp

- 日期：2026-10-12
- 状态：已接受（使用者要求：旧工程彻底独立，id 为 `cpp`，放到实践目录，与新架构形式上切割；新界面只调用旧版的编译成果）
- 取代：`subjects/c-plus-plus` 里尚未入库的「按钮启动本目录 Meson 产物」草案。那份草案把两套工程留在同一个目录。

## 背景

C++ 教程的学习壳已经换成 Tauri 2 + React（该应用 ADR 0060），目录与 id 仍是
`c-plus-plus`，知识点前缀仍是 `cpp.`。gtkmm / Meson 那一整棵源码当时还留在同一目录里，
只是不再被 `app.json` 启动。两套构建、两份窗口标题、两个都叫 `athena-c-plus-plus` 的
进程挤在一起，形式上没有切开。

使用者要的是旧工程自己成为一个应用：id `cpp`，放在 `practice/`，新教程只留一个运行入口，
去启动旧工程已经编出来的程序。

## 决策

1. **旧窗口是 `practice/cpp`。** id、目录、进程都是 `cpp` / `athena-cpp`。它是项目应用
   （仓库 ADR 0060）：保留能跑的 gtkmm 窗口，不承担课程掌握度，不进 pnpm / Cargo
   工作区（与 `pocket_cube` 一样，ADR 0140）。不挂靠 `c-plus-plus`。
2. **课程仍是 `subjects/c-plus-plus`。** Tauri 壳、课表、实验案例、`progress/learning.db`
   留在那里。知识点前缀 `cpp.` 不改。
3. **源码不互相 include。** 新壳不读旧工程的 `athena.json`，也不把旧工程的源文件编进自己。
   新课自己用到的六个实验案例留一份在 `subjects/c-plus-plus/resources/cases/`。
4. **新壳只启动旧工程的编译成果。** 侧栏入口按固定相对路径查找
   `practice/cpp/build/` 下的 `athena-cpp`（以及还没按新名字重编时的 `athena-c-plus-plus`）。
   不接受调用方传入路径，不在点击时跑 Meson，不提供任意命令。Windows 上启动前把
   `C:\msys64\mingw64\bin` 放到 PATH 前面，因为本机这份已经编好的程序链的是 mingw64 的 GTK。
5. **进度分开。** 启动旧窗口时 `ATHENA_CPP_ROOT` 指向 `practice/cpp`。课程的
   `progress/learning.db` 只由新壳写入。

## 后果

- 发版工作流里原来从 `subjects/c-plus-plus` 打的 gtkmm 安装包，改从 `practice/cpp` 打。
- 搬过目录之后，旧的 Meson `build/` 里记的是搬之前的绝对路径；下次编译要
  `meson setup build --reconfigure`。已经编好的可执行文件可以先跑。
- 这是应用之间唯一允许的路径：新壳知道仓库里 `practice/cpp` 的编译产物在哪。除此之外
  仍不引用对方的源码与内容（ADR 0032）。
