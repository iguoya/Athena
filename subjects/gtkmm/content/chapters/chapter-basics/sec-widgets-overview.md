---
chapter: chapter-basics
section: sec-widgets-overview
upstream-sha: bfdbd152c564bbfd0532c6da6b56e7565687b1a2ad23cc3a5aa0f3203c413bad
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Widgets
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-widgets-overview 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> gtkmm applications consist of windows containing widgets, such as buttons
> and text boxes. In some other systems, widgets are called "controls". For
> each widget in your application's windows, there is a C++ object in your
> application's code. So you just need to call a method of the widget's class
> to affect the visible widget.

gtkmm 应用由窗口组成，窗口里放着控件（widget），比如按钮和文本框。在某些别的
系统里，控件被叫作「control」。应用窗口里的每个控件，都对应应用代码里的一个
C++ 对象——想改变屏幕上看到的控件，只需调用该控件类的方法。

> Widgets are arranged inside container widgets such as frames and notebooks,
> in a hierarchy of widgets within widgets. Some of these container widgets,
> such as Gtk::Grid, are not visible - they exist only to arrange other
> widgets. Here is some example code that adds 2 Gtk::Button widgets to a
> Gtk::Box container widget:

控件放在容器控件里（比如 frame 和 notebook），形成「控件套控件」的层次结构。
有些容器控件（比如 Gtk::Grid）本身不可见——它们存在的意义就是排列其他控件。
下面的示例代码把 2 个 Gtk::Button 控件加进 Gtk::Box 容器控件：

```cpp
m_box.append(m_Button1);
m_box.append(m_Button2);
```

> and here is how to add the Gtk::Box, containing those buttons, to a
> Gtk::Frame, which has a visible frame and title:

下面这行把装着这两个按钮的 Gtk::Box 加进 Gtk::Frame——一个带可见边框和标题
的容器：

```cpp
m_frame.set_child(m_box);
```

> Most of the chapters in this book deal with specific widgets. See the
> Container Widgets section for more details about adding widgets to
> container widgets.

本书的大多数章节都在讲具体控件。关于把控件加入容器控件的更多细节，参见
Container Widgets 一节。

> Although you can specify the layout and appearance of windows and widgets
> with C++ code, you will probably find it more convenient to design your
> user interfaces with .ui XML files and load them at runtime with
> Gtk::Builder. See the Gtk::Builder chapter.

虽然可以用 C++ 代码指定窗口和控件的布局与外观，但用 .ui XML 文件设计界面、
运行时经 Gtk::Builder 加载，通常更方便。参见 Gtk::Builder 一章。

> Although gtkmm widget instances have lifetimes and scopes just like those
> of other C++ classes, gtkmm has an optional time-saving feature that you
> will see in some of the examples. The Gtk::make_managed() allows you to
> create a new widget and state that it will become owned by the container
> into which you place it. This allows you to create the widget, add it to
> the container and not be concerned about deleting it, since that will occur
> when the parent container (which may itself be managed) is deleted. You can
> learn more about gtkmm memory management techniques in the Memory
> Management chapter.

尽管 gtkmm 控件实例和其他 C++ 类一样有生命周期和作用域，gtkmm 提供了一个可选
的省事特性，你会在一些示例里见到：Gtk::make_managed() 让你创建新控件的同时
声明它将归你放入的那个容器所有。于是你创建控件、加进容器之后就不必操心删除
——父容器（它自己可能也是被管理的）删除时自会处理。gtkmm 内存管理技术的更多
内容见 Memory Management 一章。
