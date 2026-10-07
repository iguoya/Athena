# C GUI Lab

C 语言 GUI 框架对比实验室（practice 应用，ADR 0060 判据：做能跑的东西，不建进度库、
教学规范不生效）。同一件事用三个框架各做一遍——「体现各自美观潜力的样式程序」——
并用 Electron 母体统一启动，供并排对比显示效果。

## 结构

```
launcher/     Electron 母体启动器（画廊 UI，spawn 三个原生程序与官方 demo）
apps/
  gtk-style/    GTK4 + libadwaita + CSS 样式程序（纯 C）
  imgui-style/  Dear ImGui 样式程序（C++，原因见下）
  lvgl-style/   LVGL + SDL2 样式程序（纯 C）；--demo 进入官方 widgets 合集
  raygui-demo/  raygui 官方控件套件（vendor 单头文件 + raylib）
  nuklear-demo/ Nuklear 官方 SDL2/OpenGL2 演示（vendor 单头文件）
third_party/   imgui / lvgl / cimgui / raygui / nuklear 源码（不进版本库）
```

母体可调起的官方演示程序：
- **GTK 生态**（随 MSYS2 包安装，探测到才亮）：gtk4-demo、gtk4-widget-factory、
  gtk4-node-editor、adwaita-1-demo；
- **即时模式框架**：ImGui 的 ShowDemoWindow（imgui-style --demo）、
  raygui controls_test_suite、Nuklear SDL2 演示、Nuklear GDI 原生版（纯
  Win32 渲染）、microui 官方 demo（后三者的源码 vendor 于 third_party/，
  include 已就地修正；Nuklear GDI 与 microui 用 lld 链接，见下）。
- **LVGL 官方 widgets 合集未集成**：lv_demo_widgets 在本环境死锁（灰屏未响应，
  与中文渲染死锁同为该环境的 LVGL 兼容问题），对比任务由自建橱窗承担。

## 候选清单（暂未收编）

- **libui-ng** `examples/controlgallery`（原生控件画廊）：gitee 镜像克隆在本机
  网络下长期挂起，待网络可用时 vendor 并 meson 构建。
- **IUP** sample 画廊：无 MSYS2 包，只能 SourceForge 第三方二进制（供应链信任）
  或自建其 makefile 体系；原生控件维度的空缺可先由 libui-ng 补。
- **LVGL 官方 lv_demos**：本环境死锁（见 lv_conf.h），换 9.2.2 或 Linux 再试。

## 取舍说明

- **imgui-style 用 C++ 而不是 C + cimgui**：Dear ImGui 本体是 C++，win32/dx11
  后端是官方 C++ 文件；cimgui 的后端 C 包装需要用 Lua 现场生成，不值得。
  本程序恰好演示「C++ 是 ImGui 母语」这个事实。cimgui 源码留在 third_party/ 供
  对照 C 绑定的机械命名（IgCreateContext 这类），不参与构建。
- **Electron 做母体**是本项目的主题之一（Web 技术桌面化的对照样本），不是失误；
  仓库其他应用走 Tauri 的理由（体积、内存）在这里不成立，因为对比本身就是目的。

## 构建

- 依赖 MSYS2 UCRT64：`gtk4` `libadwaita` `SDL2`（pacman 装
  `mingw-w64-ucrt-x86_64-{gtk4,libadwaita,SDL2}`），编译器用 UCRT64 的 gcc，
  不要用 PATH 里其他来源的 gcc。
- `cmake --preset ucrt64 && cmake --build --preset ucrt64`，产物在 `build/apps/`。
- 运行期 GTK/SDL 的 DLL 在 `C:\msys64\ucrt64\bin`，母体 spawn 时会把它注入 PATH。

## 已知限制与取舍

- **imgui-style 是 C++**（见上方取舍说明），gtk-style 与 lvgl-style 是纯 C。
- **lvgl-style 的中文用 lv_font_conv 预生成子集**（font_cn_20/28.c 编译进 exe，
  文本变更后重跑 scripts/gen-cjk-font.sh）：LVGL 的 tiny_ttf 与 FreeType 集成
  在这台 Windows 上栅格化首个 CJK 字形都会死循环（tiny_ttf 的 data 模式即
  subjects/machine playground 的方案，mac/Linux 成熟但同样复现）。预生成子集
  是 LVGL 社区标准做法，零运行时依赖、行为确定；代价是字符集固定。

## 验证

`python3 scripts/check.py`：结构完整性 + Electron 主进程语法 + 三个原生程序增量编译。
