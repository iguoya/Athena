---
chapter: chapter-basics
section: sec-helloworld
upstream-sha: 6d063dd9b7c5676b34a44f7f114d6be781570af5b8b6597f71585d8df3603cb9
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Hello World in gtkmm
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-helloworld 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

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
