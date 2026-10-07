# C 语言 GUI 框架对比实验室

Electron 母体统一启动的 GUI 框架对比场：收编 GTK4+Adwaita、ImGui、LVGL、
raygui/Nuklear、microui 等框架的官方演示与样式橱窗，横向比较观感与手感。

- `third_party/` 是各框架源码，不入库（应用内 `.gitignore` 忽略），按 `AGENTS.md`
  的说明自行准备。
- 启动：`launcher open c-gui-lab`（`app.json` 声明）。
- 实验场性质，不建进度库（ADR 0060）。
