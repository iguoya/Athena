---
chapter: chapter-basics
section: sec-signals-overview
upstream-sha: 0d1d39b0f66c51607dbd350d15b0dd34f9050d8615c08ea6774ef37fec938e69
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Signals
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-signals-overview 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> gtkmm, like most GUI toolkits, is event-driven. When an event occurs, such
> as the press of a mouse button, the appropriate signal will be emitted by
> the Widget that was pressed. Each Widget has a different set of signals
> that it can emit. To make a button click result in an action, we set up a
> signal handler to catch the button's "clicked" signal.

与大多数 GUI 工具集一样，gtkmm 是事件驱动的。事件发生时——比如按下鼠标键——
被按下的 Widget 会发出相应的信号。每种 Widget 能发出的信号各不相同。要让一次
按钮点击触发一个动作，我们设置一个信号处理器（signal handler）来捕获按钮的
「clicked」信号。

> gtkmm uses the libsigc++ library to implement signals. Here is an example
> line of code that connects a Gtk::Button's "clicked" signal with a signal
> handler called "on_button_clicked":

gtkmm 用 libsigc++ 库实现信号。下面这行示例代码把 Gtk::Button 的「clicked」
信号连接到名为 on_button_clicked 的信号处理器：

```cpp
m_button1.signal_clicked().connect( sigc::mem_fun(*this,
  &HelloWorld::on_button_clicked) );
```

> For more detailed information about signals, see the appendix.

信号的详细信息见附录（Signals）。

> For information about implementing your own signals rather than just
> connecting to the existing gtkmm signals, see the appendix.

关于如何实现自己的信号（而不只是连接现有的 gtkmm 信号），见附录（Creating
your own signals）。
