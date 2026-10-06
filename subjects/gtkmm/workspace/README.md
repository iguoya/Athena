# 工作集（workspace）

学习者自己的地盘：**骨架实验的学习者副本**和**自由学习测试项目**都放这里。
`demos/` 是清单（`content/demos.json`）引用的只读骨架，事实源；这里的东西随便改、
随时删，删了可以从骨架重新复制，或照着模板重写。

## 约定

- **一个学习集一个目录、一个独立 CMake 工程**：自己配置、自己构建，互不引用；
  工具链与 `demos/` 相同（`gtkmm-4.0`、C++17、MSYS2 UCRT64）。
- **不进清单**：工作集不是教学实体，不登记 `demos.json`、不并入 `demos/CMakeLists.txt`、
  不要求实现演示 RPC 协议（应用 ADR 0001 只约束清单实体）。
- **骨架副本落点**：壳实现「复制到工作区 / 一键重置」后，`exp.*` 的学习者副本
  固定放在 `workspace/<实验 id>/`（如 `workspace/exp.buttons/`），重置 = 删掉重拷。
- **构建产物不入库**：各集的 `build/` 已在应用 `.gitignore` 里；源码正常提交。

## 建一个新学习集

1. 复制 `hello-gtkmm/`（最小可编译模板）为你的目录名；
2. 改目录名与 `project()` 名；
3. 构建（在配套的 MSYS2 环境的 Shell 里，如 MINGW64；`-G Ninja` 必须显式给，
   否则 Windows 上 CMake 默认选 Visual Studio 生成器、用 MSVC 编 MinGW ABI 的
   gtkmm 必然失败）：

   ```sh
   cmake -G Ninja -S <你的集> -B <你的集>/build
   cmake --build <你的集>/build
   ./<你的集>/build/<产物>.exe
   ```

   环境自检：`pkg-config --modversion glib-2.0 glibmm-2.68` 两个版本要配套
   （如都是 2.90.x）。glib 与 glibmm 大版本不匹配说明环境处于部分升级状态，
   会出现 G_DECLARE_FINAL_TYPE 头文件冲突，`pacman -Syu` 对齐即可。

## 用 VS2022 打开

工作集根目录已配好 VS2022 的 CMake 集成三件套（`CMakeLists.txt` 顶层工程、
`CMakePresets.json`、`launch.vs.json`）：

1. VS2022 →「打开文件夹」选 `workspace/`（或资源管理器右键「通过 Visual Studio 打开」）；
2. 右上角配置下拉选 **MSYS2 MINGW64 GCC**（已验证配套；UCRT64 待 `pacman -Syu` 对齐），
   VS 自动 configure；
3. `Ctrl+Shift+B` 构建全部学习集，产物统一落在 `build/` 根；
4. F5 启动 `launch.vs.json` 里登记的目标（新集记得在 `CMakeLists.txt` 顶层
   `add_subdirectory` 一行、在 `launch.vs.json` 加一段配置）。

命令行同款：`cmake --preset msys2-mingw64 && cmake --build --preset msys2-mingw64`。

## 从骨架开一个实验副本

```sh
cp -r demos/buttons-lab workspace/exp.buttons
cmake -G Ninja -S workspace/exp.buttons -B workspace/exp.buttons/build
cmake --build workspace/exp.buttons/build
```

想重来：删掉 `workspace/exp.buttons/` 再拷一遍即可；骨架在 `demos/` 里永远原样。
