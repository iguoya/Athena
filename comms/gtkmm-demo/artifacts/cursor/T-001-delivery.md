# T-001 交付说明

## 演示做了什么

窗口里一个按钮、一行提示、一块可选中的日志。启动后日志自己往下长；点一次按钮追加两行；点关闭再追加一行。每一行同时用 `rpc::signal` 上报。

协议与 `demos/buttons` 相同：`signal_activate` 里 `show()`、发 `ready`、监听 `initialize` / `ping` / `shutdown`。没有用 `make_window_and_run`，因为那个函数会在激活回调里才构造窗口，壳的拉起方式对不上。窗口是在 `run()` 之前构造的，和 buttons 一样。

`source_dir` 在集成时建议为 `demos/basics-signals`（与 `rpc.hpp` 同级，CMake 的 `..` 才能找到它）。草稿现在在 `artifacts/cursor/demo-basics-signals/`。

## 预期日志（已实测）

临时探针在激活后调用 `button.activate()`，再 `close()`。顺序如下，界面序号从 1 起：

```
1  window constructed
2  window activate
3  window map
4  window show
5  button handler A
6  button handler B
7  window close_request
```

`constructed` 不是 GTK 信号，是构造函数最后一行自己记的。`activate` 记在 `signal_activate` 处理器的开头、`show()` 之前。`map` 在 `show` 前面，是因为这两个信号都是 Run First：`show` 的默认处理器先把窗口映射，用户连上的 `show` 处理器才跑。`close_request` 的 `connect` 必须带第二个参数 `false`（返回 bool 的代理没有默认值）；槽返回 `false`，默认处理器才会真正关窗。

`--self-check` 只构造窗口，退出码 0，stdout 上有一行 `constructed`。gtkmm 4.24.0，MINGW64。

## 模拟的简化

`SignalOrderSim` 只画「点击 → 处理器 A → 处理器 B」。先选预测再运行，选对选错都有反馈。不画 GDK 分发与捕获，也不画 show / map。粘进 `simulations.tsx` 时只取函数，并给 `SimulationView` 加 `case "signal-order"`。

## 没写进代码的 API

下列名字核对过 gtkmm 4.24 头文件，并在上面的探针里出现过，没有拿不准却写进去的调用。

`make_window_and_run` 的实现（`application.h`）是在 `signal_activate` 里构造窗口再 `present()`。那条路径上「构造完成」会发生在激活开始之后。本演示为了跟 buttons 的协议一致，把窗口放在 `run()` 之前构造，所以日志是先 `constructed` 再 `activate`。
