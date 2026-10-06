---
chapter: chapter-basics
section: sec-basics-simple-example
upstream-sha: 648df7687303be70b5256a0a3c44a84f319c3ca2d69871646f4a6c0fae957365
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Simple Example
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-basics-simple-example 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> To begin our introduction to gtkmm, we'll start with the simplest program
> possible. This program will create an empty 200 x 200 pixel window.

在开始介绍 gtkmm 之前，我们先从最简单的程序入手。这个程序会创建一个空的
200 × 200 像素的窗口。

> Source Code
> File: base.cc (For use with gtkmm 4)

源代码文件：base.cc（适用于 gtkmm 4）

```cpp
#include <gtkmm.h>

class MyWindow : public Gtk::Window
{
public:
  MyWindow();
};

MyWindow::MyWindow()
{
  set_title("Basic application");
  set_default_size(200, 200);
}

int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.examples.base");

  return app->make_window_and_run<MyWindow>(argc, argv);
}
```

> We will now explain each part of the example

下面逐段解释这个示例。

```cpp
#include <gtkmm.h>
```

> All gtkmm programs must include certain gtkmm headers; gtkmm.h includes the
> entire gtkmm kit. This is usually not a good idea, because it includes a
> megabyte or so of headers, but for simple programs, it suffices.

所有 gtkmm 程序都必须包含某些 gtkmm 头文件；gtkmm.h 把整套 gtkmm 头文件全部
包含进来。这通常不是好做法——它引入了大约一兆字节的头文件——但对简单程序
来说够用了。

> The next part of the program:

程序的下一部分：

```cpp
class MyWindow : public Gtk::Window
{
public:
  MyWindow();
};

MyWindow::MyWindow()
{
  set_title("Basic application");
  set_default_size(200, 200);
}
```

> defines the MyWindow class. Its default constructor sets the window's title
> and default (initial) size.

定义了 MyWindow 类。它的默认构造函数设置窗口标题和默认（初始）尺寸。

> The main() function's first statement:

main() 函数的第一条语句：

```cpp
auto app = Gtk::Application::create("org.gtkmm.examples.base");
```

> creates a Gtk::Application object, stored in a Glib::RefPtr smartpointer.
> This is needed in all gtkmm applications. The create() method for this
> object initializes gtkmm.

创建一个 Gtk::Application 对象，保存在 Glib::RefPtr 智能指针里。每个 gtkmm
程序都需要它；该对象的 create() 方法完成 gtkmm 的初始化。

> The last line creates and shows a window and enters the gtkmm main
> processing loop, which will finish when the window is closed. Your main()
> function will then return with an appropriate success or error code. The
> argc and argv arguments, passed to your application on the command line,
> can be checked when make_window_and_run() is called, but this simple
> application does not use those arguments.

最后一行创建并显示窗口，然后进入 gtkmm 主处理循环，窗口关闭时循环结束，main()
函数随之返回相应的成功或错误码。命令行传入的 argc 和 argv 参数可以在调用
make_window_and_run() 时处理，但这个简单程序没有用到它们。

```cpp
return app->make_window_and_run<MyWindow>(argc, argv);
```

> After putting the source code in base.cc you can compile the above program
> with gcc using:

把源码存为 base.cc 之后，可以用 gcc 这样编译：

```bash
g++ base.cc -o base `pkg-config --cflags --libs gtkmm-4.0` -std=c++17
```

> Note that you must surround the pkg-config invocation with backquotes.
> Backquotes cause the shell to execute the command inside them, and to use
> the command's output as part of the command line. Note also that base.cc
> must come before the pkg-config invocation on the command line. -std=c++17
> is necessary only if your compiler is not C++17 compliant by default.

注意：pkg-config 的调用必须用反引号包起来——反引号让 shell 先执行其中的命令，
并把命令的输出拼进命令行。还要注意 base.cc 必须写在 pkg-config 调用之前。
只有当编译器默认不遵循 C++17 时才需要 -std=c++17。
