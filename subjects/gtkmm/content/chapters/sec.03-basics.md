<!--
来源：Programming with gtkmm 4 · Chapter 3. Basics
原文：https://gnome.pages.gitlab.gnome.org/gtkmm-documentation/chapter-basics.html
     （含 sec-headers-and-linking / sec-widgets-overview / sec-signals-overview /
      sec-basics-ustring / sec-basics-gobj-and-wrap / sec-helloworld 各节页）
原作：Murray Cumming，GFDL-1.2+（许可全文与义务说明见 content/license.md）
性质：逐段对照翻译稿。引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
-->

# 第 3 章 · Basics（基础）

## Simple Example（简单示例）

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

## Headers and Linking（头文件与链接）

> Although we have shown the compilation command for the simple example, you
> really should use the Meson build system. The examples used in this book
> are included in the gtkmm-documentation package, with appropriate build
> files, so we won't show the build commands in future. The README file in
> gtkmm-documentation describes how to build the examples.

虽然上面给出了简单示例的编译命令，但实际开发应该使用 Meson 构建系统。本书的
示例都收录在 gtkmm-documentation 包里，并带有相应的构建文件，所以之后不再
罗列构建命令。gtkmm-documentation 的 README 文件描述了如何构建这些示例。

> To simplify compilation, we use pkg-config, which is present in all
> (properly installed) gtkmm installations. This program 'knows' what
> compiler switches are needed to compile programs that use gtkmm. The
> --cflags option causes pkg-config to output a list of include directories
> for the compiler to look in; the --libs option requests the list of
> libraries for the compiler to link with and the directories to find them
> in. Try running it from your shell-prompt to see the results on your
> system.

为了简化编译，我们使用 pkg-config——一切（正确安装的）gtkmm 环境里都有它。
这个程序「知道」编译使用 gtkmm 的程序需要哪些编译开关。--cflags 让
pkg-config 输出编译器的头文件搜索目录列表；--libs 请求链接库列表及其所在
目录。可以在 shell 里亲手跑一下，看看你系统上的输出。

> However, this is even simpler when using the dependency() function in a
> meson.build file with Meson. For instance:

而用 Meson 时，在 meson.build 文件里调用 dependency() 函数还要更简单。例如：

```meson
gtkmm_dep = dependency('gtkmm-4.0', version: '>= 4.6.0')
```

> This checks for the presence of gtkmm and defines gtkmm_dep for use in your
> meson.build files. For instance:

这一句会检查 gtkmm 是否可用，并定义出 gtkmm_dep 供 meson.build 使用。例如：

```meson
exe_file = executable('my_program', 'my_source1.cc', 'my_source2.cc',
  dependencies: gtkmm_dep,
  win_subsystem: 'windows',
)
```

> gtkmm-4.0 is the name of the current stable API. There are older APIs
> called gtkmm-2.4 and gtkmm-3.0 which install in parallel when they are
> available. There are several versions of gtkmm-2.4, such as gtkmm 2.10 and
> there are several versions of the gtkmm-3.0 API. Note that the API name does
> not change for every version because that would be an incompatible API and
> ABI break. There might be a future gtkmm-5.0 API which would install in
> parallel with gtkmm-4.0 without affecting existing applications.

gtkmm-4.0 是当前稳定 API 的名字。还有更老的 API 叫 gtkmm-2.4 和 gtkmm-3.0，
如果系统里有的话，它们与 gtkmm-4.0 并行安装。gtkmm-2.4 有多个版本（比如
gtkmm 2.10），gtkmm-3.0 API 也有多个版本。注意：API 名字不会随每个版本改变，
因为改名就意味着不兼容的 API/ABI 断裂。将来可能出现 gtkmm-5.0 API，它将与
gtkmm-4.0 并行安装，不影响现有应用。

> If you start by experimenting with a small application that you plan to use
> just for yourself, it's easier to start with a meson.build similar to the
> meson.build files in the Building applications chapter.

如果你想先做一个自用的小应用练手，直接参考「Building applications」一章里的
meson.build 文件来起步会更容易。

> If you use the older Autotools build system, see also the GNU site. It has
> more information about autoconf and automake. There are also some books
> describing Autotools: "GNU Autoconf, Automake, and Libtool" by Gary Vaughan
> et al. and "Autotools, A Practitioner's Guide to GNU Autoconf, Automake,
> and Libtool" by John Calcote.

如果你用的是更老的 Autotools 构建系统，另请参阅 GNU 网站，那里有关于
autoconf 和 automake 的更多信息。也有几本书专门讲 Autotools：Gary Vaughan 等
人的《GNU Autoconf, Automake, and Libtool》，以及 John Calcote 的
《Autotools, A Practitioner's Guide to GNU Autoconf, Automake, and Libtool》。

## Widgets（控件）

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

## Signals（信号）

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

## Glib::ustring

> You might be surprised to learn that gtkmm doesn't use std::string in its
> interfaces. Instead it uses Glib::ustring, which is so similar and
> unobtrusive that you could actually pretend that each Glib::ustring is a
> std::string and ignore the rest of this section. But read on if you want to
> use languages other than English in your application.

你可能会惊讶：gtkmm 的接口里用的不是 std::string，而是 Glib::ustring。它与
std::string 相似到几乎不引人注意的程度——你完全可以假装每个 Glib::ustring
就是 std::string，然后跳过本节剩下的部分。但如果你的应用要用英语以外的语言，
请往下读。

> std::string uses 8 bits per character, but 8 bits aren't enough to encode
> languages such as Arabic, Chinese, and Japanese. Although the encodings for
> these languages have been specified by the Unicode Consortium, the C and
> C++ languages do not yet provide any standardized Unicode support for UTF-8
> encoding. GTK and GNOME chose to implement Unicode using UTF-8, and that's
> what is wrapped by Glib::ustring. It provides almost exactly the same
> interface as std::string, along with automatic conversions to and from
> std::string.

std::string 每个字符 8 个比特，而 8 个比特不足以编码阿拉伯文、中文、日文这些
语言。这些语言的编码虽已由 Unicode 联盟制定，但 C 和 C++ 语言至今没有为 UTF-8
编码提供标准化的 Unicode 支持。GTK 和 GNOME 选择用 UTF-8 实现 Unicode，
Glib::ustring 包装的正是它。它提供的接口与 std::string 几乎完全一致，并带有
与 std::string 的双向自动转换。

> One of the benefits of UTF-8 is that you don't need to use it unless you
> want to, so you don't need to retrofit all of your code at once.
> std::string will still work for 7-bit ASCII strings. But when you try to
> localize your application for languages like Chinese, for instance, you
> will start to see strange errors, and possible crashes. Then all you need
> to do is start using Glib::ustring instead.

UTF-8 的一个好处是：不用它可以不用，不必一次性改造全部代码。对 7 位 ASCII
字符串，std::string 依然可用。但当你开始把应用本地化成中文之类的语言时，就会
开始见到奇怪的错误，甚至崩溃。到那时，改用 Glib::ustring 就好。

> Note that UTF-8 isn't compatible with 8-bit encodings like ISO-8859-1. For
> instance, German umlauts are not in the ASCII range and need more than 1
> byte in the UTF-8 encoding. If your code contains 8-bit string literals, you
> have to convert them to UTF-8 (e.g. the Bavarian greeting "Grüß Gott" would
> be "Gr\xC3\xBC\xC3\x9F Gott").

注意：UTF-8 与 ISO-8859-1 这类 8 位编码不兼容。比如德语的变音符不在 ASCII
范围内，UTF-8 编码下需要不止 1 个字节。如果代码里有 8 位字符串字面量，必须
转换成 UTF-8（例如巴伐利亚问候语「Grüß Gott」要写成
"Gr\xC3\xBC\xC3\x9F Gott"）。

> You should avoid C-style pointer arithmetic, and functions such as
> strlen(). In UTF-8, each character might need anywhere from 1 to 6 bytes, so
> it's not possible to assume that the next byte is another character.
> Glib::ustring worries about the details of this for you so you can use
> methods such as Glib::ustring::substr() while still thinking in terms of
> characters instead of bytes.

应当避免 C 风格的指针运算，以及 strlen() 之类的函数。UTF-8 中一个字符可能占
1 到 6 个字节，不能假定下一个字节就是下一个字符。Glib::ustring 替你操心这些
细节：你可以继续用 Glib::ustring::substr() 之类的方法，按字符而不是按字节
思考。

> Unlike the Windows UCS-2 Unicode solution, this does not require any
> special compiler options to process string literals, and it does not result
> in Unicode executables and libraries which are incompatible with ASCII
> ones.

与 Windows 的 UCS-2 Unicode 方案不同，这套做法处理字符串字面量不需要任何特殊
编译选项，也不会产生与 ASCII 版本互不兼容的 Unicode 可执行文件和库。

> Reference

（参考文档链接见原页面末尾。）

## Mixing C and C++ APIs（混用 C 与 C++ API）

> You can use C APIs which do not yet have convenient C++ interfaces. It is
> generally not a problem to use C APIs from C++, and gtkmm helps by providing
> access to the underlying C object, and providing an easy way to create a
> C++ wrapper object from a C object, provided that the C API is also based on
> the GObject system.

那些还没有顺手 C++ 接口的 C API 也可以用。在 C++ 里调用 C API 一般不成问题；
gtkmm 还帮了两把：让你能访问底层的 C 对象，并且在 C API 同样基于 GObject
系统的前提下，提供从 C 对象便捷创建 C++ 包装对象的途径。

> To use a gtkmm instance with a C function that requires a C GObject
> instance, use the C++ instance's gobj() function to obtain a pointer to the
> underlying C instance. For example:

要把 gtkmm 实例传给需要 C GObject 实例的 C 函数，用 C++ 实例的 gobj() 函数
拿到底层 C 实例的指针。例如：

```cpp
Gtk::Button button("example");
gtk_button_do_something_that_gtkmm_cannot(button.gobj());
```

> To obtain a gtkmm instance from a C GObject instance, use one of the many
> overloaded Glib::wrap() functions. The C instance's reference count is not
> incremented, unless you set the optional take_copy argument to true. For
> example:

反过来，要从 C GObject 实例得到 gtkmm 实例，用众多重载的 Glib::wrap() 函数
之一。除非把可选的 take_copy 参数设为 true，C 实例的引用计数不会增加。例如：

```cpp
GtkButton* cbutton = get_a_button();
Gtk::Button* button = Glib::wrap(cbutton);
button->set_label("Now I speak C++ too!");
```

> The C++ wrapper shall be explicitly deleted if

C++ 包装对象在满足以下条件时必须显式删除：

> - it's a widget or other class that inherits from Gtk::Object, and
> - the C instance has a floating reference when the wrapper is created, and
> - Gtk::manage() has not been called on it (which includes if it was created
>   with Gtk::make_managed()), or
> - Gtk::manage() was called on it, but it was never added to a parent.

- 它是控件或别的继承自 Gtk::Object 的类，且
- 创建包装对象时 C 实例带 floating reference（浮动引用），且
- 没有对它调用过 Gtk::manage()（包括用 Gtk::make_managed() 创建的情况），或者
- 调用过 Gtk::manage()，但从未把它加进任何父容器。

> Glib::wrap() binds the C and C++ instances to each other. Don't delete the
> C++ instance before you want the C instance to die.

Glib::wrap() 把 C 实例和 C++ 实例绑定在一起：不希望 C 实例死掉之前，别删
C++ 实例。

> In all other cases the C++ instance is automatically deleted when the last
> reference to the C instance is dropped. This includes all Glib::wrap()
> overloads that return a Glib::RefPtr.

在其他所有情况下，C 实例的最后一个引用被释放时，C++ 实例会自动删除——包括
所有返回 Glib::RefPtr 的 Glib::wrap() 重载。

## Hello World in gtkmm（gtkmm 版 Hello World）

> We've now learned enough to look at a real example. In accordance with an
> ancient tradition of computer science, we now introduce Hello World, a la
> gtkmm:

我们已经学够了，可以看一个真正的例子了。按照计算机科学的古老传统，现在介绍
gtkmm 风格的 Hello World：

> Source Code
> File: helloworld.h (For use with gtkmm 4)

源代码文件：helloworld.h（适用于 gtkmm 4）

```cpp
#ifndef GTKMM_EXAMPLE_HELLOWORLD_H
#define GTKMM_EXAMPLE_HELLOWORLD_H

#include <gtkmm/button.h>
#include <gtkmm/window.h>

class HelloWorld : public Gtk::Window
{

public:
  HelloWorld();
  ~HelloWorld() override;

protected:
  //Signal handlers:
  void on_button_clicked();

  //Member widgets:
  Gtk::Button m_button;
};

#endif // GTKMM_EXAMPLE_HELLOWORLD_H
```

> File: helloworld.cc (For use with gtkmm 4)

源代码文件：helloworld.cc（适用于 gtkmm 4）

```cpp
#include "helloworld.h"
#include <iostream>

HelloWorld::HelloWorld()
: m_button("Hello World") // creates a new button with label "Hello World".
{
  // Sets the margin around the button.
  m_button.set_margin(10);

  // When the button receives the "clicked" signal, it will call the
  // on_button_clicked() method defined below.
  m_button.signal_clicked().connect(sigc::mem_fun(*this,
    &HelloWorld::on_button_clicked));

  // This packs the button into the Window (a container).
  set_child(m_button);
}

HelloWorld::~HelloWorld()
{
}

void HelloWorld::on_button_clicked()
{
  std::cout << "Hello World" << std::endl;
}
```

> File: main.cc (For use with gtkmm 4)

源代码文件：main.cc（适用于 gtkmm 4）

```cpp
#include "helloworld.h"
#include <gtkmm/application.h>

int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.example");

  //Shows the window and returns when it is closed.
  return app->make_window_and_run<HelloWorld>(argc, argv);
}
```

> Try to compile and run it before going on. You should see something like
> this:

继续往下读之前，先编译并运行它。你会看到类似这样的东西：

> Figure 3.1. Hello World

图 3.1 Hello World

> Pretty thrilling, eh? Let's examine the code. First, the HelloWorld class:

相当激动人心吧？我们来读代码。先看 HelloWorld 类：

```cpp
class HelloWorld : public Gtk::Window
{
public:
  HelloWorld();
  ~HelloWorld() override;

protected:
  //Signal handlers:
  void on_button_clicked();

  //Member widgets:
  Gtk::Button m_button;
};
```

> This class implements the "Hello World" window. It's derived from
> Gtk::Window, and has a single Gtk::Button as a member. We've chosen to use
> the constructor to do all of the initialization work for the window,
> including setting up the signals. Here it is, with the comments omitted:

这个类实现「Hello World」窗口：派生自 Gtk::Window，有一个 Gtk::Button 成员。
我们选择在构造函数里完成窗口的全部初始化工作，包括设置信号。以下是省略注释
后的构造函数：

```cpp
HelloWorld::HelloWorld()
: m_button("Hello World")
{
  m_button.set_margin(10);
  m_button.signal_clicked().connect(sigc::mem_fun(*this,
    &HelloWorld::on_button_clicked));
  set_child(m_button);
}
```

> Notice that we've used an initializer statement to give the m_button object
> the label "Hello World".

注意我们用了初始化列表，把标签「Hello World」交给 m_button 对象。

> Next we call the Button's set_margin() method. This sets the amount of
> space around the button.

接着调用 Button 的 set_margin() 方法，设置按钮四周留出的空间大小。

> We then hook up a signal handler to m_button's clicked signal. This prints
> our friendly greeting to stdout.

然后把信号处理器挂到 m_button 的 clicked 信号上，向标准输出打印友好的问候语。

> Next, we use the Window's set_child() method to put m_button in the Window.
> The set_child() method places the Widget in the Window.

再用 Window 的 set_child() 方法把 m_button 放进窗口——set_child() 负责把
Widget 放入 Window。

> Now let's look at our program's main() function. Here it is, without
> comments:

现在看程序的 main() 函数，省略注释后如下：

```cpp
int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.example");
  return app->make_window_and_run<HelloWorld>(argc, argv);
}
```

> First we instantiate an object stored in a Glib::RefPtr smartpointer called
> app. This is of type Gtk::Application. Every gtkmm program must have one of
> these.

先实例化一个对象，存进名为 app 的 Glib::RefPtr 智能指针，类型是
Gtk::Application——每个 gtkmm 程序都必须有一个。

> Next we call make_window_and_run() which creates an object of our
> HelloWorld class, shows that Window and starts the gtkmm event loop. During
> the event loop gtkmm idles, waiting for actions from the user, and
> responding appropriately. When the user closes the Window,
> make_window_and_run() will return, causing our main() function to return.
> The application will then finish.

接着调用 make_window_and_run()：创建一个 HelloWorld 类的对象，显示该窗口并
启动 gtkmm 事件循环。事件循环期间 gtkmm 待机等待用户操作并作出响应；用户关闭
窗口时 make_window_and_run() 返回，main() 随之返回，应用结束。

> Like the simple example we showed earlier, this Hello World program does
> not use the command-line parameters.

与前面的简单示例一样，这个 Hello World 程序没有使用命令行参数。
