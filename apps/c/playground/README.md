# 内存小程序（保留）

这是最初用 LVGL + SDL2 画窗口的 C 语言实验壳。主程序图谱入口已经改成
Qt Quick / QML 教学应用（见上一级 [`../README.md`](../README.md)），
**本目录不再被 `app.json` 拉起**。先原样保留：以后「看见内存」的实验窗口
仍可能从这里长出来，不要删。

## 构建

```sh
cmake -S apps/c/playground -B apps/c/playground/build
cmake --build apps/c/playground/build
./apps/c/playground/build/athena-c
```

窗口后端需要 `vendor/lvgl/` 和 SDL2，见 [vendor/README.md](vendor/README.md)。
两者任一缺失时会编译成占位实现——能启动、不开窗口。

## 中文显示

界面中文由 `src/cjk_font.c` 加载系统字体。不要改用 LVGL 内置的
`lv_font_simsun_16_cjk`（字表偏日文与繁体，简体大面积缺字）。
