# T-002 交付说明

## 演示做了什么

窗口里一行三个按钮：甲、乙、丙。下面四个开关：甲 hexpand、乙 hexpand、乙居中、间距 16。标签上报 `rpc::signal("layout","widths","a=..;b=..;c=..")`，文字和上报是同一串。

甲的开关是为了第二个预测点：两个按钮都 hexpand。任务书里的三个问题都能在这四个开关上摆出来。

读数用 `get_width()`。它是交给 size-allocate 的内容宽，不含主题内边距。realize 之后用 `add_tick_callback` 读：拖窗口不会发属性通知，tick 在每帧能看到上一帧已经分配好的宽度；数字没变就不上报。第一帧还是 0，跳过。

`source_dir` 集成时用 `demos/container-box`（与 `rpc.hpp` 同级）。草稿在 `artifacts/cursor/demo-container-box/`。同目录的 `spec.json` 这一版是 T-002 的，T-001 的草稿已被集成进 `guide/gtkmm/`。

## 预期读数（已实测）

gtkmm 4.24.0，MINGW64。窗口默认 560、边距 12 时，按钮行宽 536。三个按钮自然外框都是 52，`get_width()` 是 18，差 34，是内边距加边框，不随分配变。完整表在 `artifacts/cursor/T-002-probe.txt`。

演示刚打开、开关全关，上报：

```
layout widths a=18;b=18;c=18
```

1. 只开「乙 hexpand」：多余宽度都进乙。行宽 536 时 `a=18;b=398;c=18`。再拉宽，只有 b 变大。
2. 甲、乙都开 hexpand：多余宽度均分。同一行宽下 `a=208;b=208;c=18`。除不尽时多 1 像素给更靠前的按钮（三开、行宽 800 时见过 `233,233,232`）。
3. 只开「乙 hexpand」和「乙居中」：三个 `get_width()` 都停在 18。乙的外框仍是 52，居中画在变宽的那一档里，丙被推向右边。只开居中、不开 hexpand 时，和全关一样。
4. 「间距 16」从相邻按钮之间扣像素。只开乙 hexpand 时，b 从 398 降到 366，少的 32 就是两段间距。

像素随主题和窗口宽度变。观察题只问谁变，不问具体数字。

## 模拟的简化

`BoxLayoutSim` 先选「多余宽度归谁」，再运行；然后用滑块和同样的四个开关看另外两种情况。外框按固定自然宽度 48 再增长，不是 GTK 的测量。乙居中时虚线是占位，实心块才是按钮。真机标签比外框少一圈内边距。粘进 `simulations.tsx` 时只取函数，并给 `SimulationView` 加 `case "box-layout"`。

## 核实过的 API

下列调用对过 gtkmm 4.24 头文件，并在探针或演示进程里跑过。没有拿不准却写进正确选项的行为。

`Gtk::Box`、`set_spacing`、`set_hexpand`、`set_halign`、`Gtk::Align::FILL`、`Gtk::Align::CENTER`、`get_width`、`signal_realize`、`add_tick_callback`、`Gtk::CheckButton::signal_toggled`、`get_active`。`compute_bounds` 只在探针里用来区分外框和内容宽，没有放进演示。
