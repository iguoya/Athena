import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

AL, UW = "sec-application-lifetime", "sec-using-a-gtkmm-widget"

INPAGE = [
    dict(id="rt30-al-1", page=AL, pos=2,
         stem="下面的 main() 执行到最后一行时，MyWindow 对象的生命周期是怎样的？",
         code="""
int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.example");
  return app->make_window_and_run<MyWindow>(argc, argv);
}""",
         right="创建并显示窗口，窗口关闭时被它删除，然后函数才返回",
         wrong=["只创建窗口，返回之前必须由程序员自己 delete 窗口",
                "窗口关闭后函数仍不返回，直到调用 Application::quit()",
                "窗口一显示出来函数就立即返回，窗口由事件循环维持"],
         why="只有一个主窗口的应用可以用 make_window_and_run()：它创建并显示窗口，窗口关闭时删除窗口，并返回给调用者。关闭可能由用户触发，也可能是你的代码调用 Gtk::Window::close()。",
         ref="推荐技术：make_window_and_run() 创建并显示窗口，窗口关闭时删除它并返回"),
    dict(id="rt30-al-2", page=AL, pos=0,
         stem="窗口里有未保存的更改，想在用户点关闭按钮时拦下来，应当重写哪个函数？",
         right="Gtk::Window::on_close_request()",
         wrong=["Gtk::Window::close()，它负责拦截用户发出的关闭请求",
                "Gtk::Widget::on_hide()，窗口隐藏之前先调用它",
                "Gtk::Application::quit()，在这里决定是否真的退出"],
         why="文档给出的做法是重写 Gtk::Window::on_close_request()，例如有未保存的更改时阻止用户关闭窗口。Gtk::Window::close() 是反方向的：由你的代码主动请求关闭窗口。",
         ref="推荐技术：重写 Gtk::Window::on_close_request() 可阻止用户关闭窗口"),
    dict(id="rt30-al-3", page=AL, pos=3,
         stem="本节为什么建议用 Meson 来构建 gtkmm 程序？",
         right="它分析 C/C++ 文件的依赖，生成 build.ninja 以便按序编译",
         wrong=["它把所有源文件合并成一个文件，所以不需要再分头编译",
                "它在运行时检查信号连接是否正确，并自动补上缺失的连接",
                "它替你编写窗口类的代码，只剩下 main() 要手写"],
         why="文档的说法：Meson 会检查 C 和 C++ 文件，确定它们之间如何互相依赖，并生成 build.ninja 之类的文件，使它们按正确的顺序编译；它还能自动配置软件的安装，处理大量系统差异以增强可移植性。",
         ref="推荐技术：使用 Meson，它检查文件依赖并生成 build.ninja"),
    dict(id="rt30-al-4", page=AL, pos=1,
         stem="下面这行连接，体现了本节的哪一条建议？",
         code="""
// m_child 是 MainWindow 的成员
m_child.signal_done().connect(sigc::mem_fun(*this, &MainWindow::on_child_done));""",
         right="对象通过信号和信号处理函数通信，而不是互相持有指针",
         wrong=["让主窗口持有子对象的指针，通过指针直接调用成员函数",
                "子部件的信号必须在析构函数里才能连接，以防重复连接",
                "信号处理函数只能是静态成员，不能是对象的成员函数"],
         why="文档建议创建自己的信号而不是传递指针：对象可以通过信号和信号处理函数相互通信，比持有指向彼此的指针、再调用对方的成员函数要简单明了得多。",
         ref="推荐技术：创建自己的信号而不是传递指针"),
    dict(id="rt30-al-5", page=AL, pos=3,
         stem="为自己的类定义信号时，应当使用哪种 signal 类型？",
         right="libsigc++ 描述的普通 sigc::signal",
         wrong=["gtkmm 类内部使用的那个特殊版本的信号类型",
                "Glib::SignalProxy，它是任何信号的统一写法",
                "Gtk::Signal，gtkmm 为自定义信号单独提供的类"],
         why="文档说明：gtkmm 的类使用的是 sigc::signal 的特殊版本，但你自己的信号应当使用 libsigc++ 所描述的正常 sigc::signal。",
         ref="推荐技术：自己的信号用 libsigc++ 的普通 sigc::signal"),
    dict(id="rt30-uw-1", page=UW, pos=0,
         stem="按本节描述的使用部件的步骤，下面构造函数里的三条语句依次对应哪三步？",
         code="""
ExampleWindow::ExampleWindow()
{
  m_button.set_label("Hi");
  m_button.signal_clicked().connect(sigc::mem_fun(*this, &ExampleWindow::on_click));
  m_box.append(m_button);
}""",
         right="设置属性、连接信号处理函数、装入容器",
         wrong=["声明变量、设置属性、装入容器，最后才连接信号",
                "连接信号处理函数、装入容器、设置属性",
                "装入容器、设置属性，信号稍后在 on_click 里连接"],
         why="本节列的步骤：声明部件（通常作为派生容器类的成员）、设置属性、连接需要的信号处理函数、再调用适当的函数（如 Gtk::Box::append()）把部件装入容器。示例里声明发生在类定义中，这里看到的是后三步。",
         ref="使用 gtkmm 部件：声明、设置属性、连接信号、装入容器的步骤"),
    dict(id="rt30-uw-2", page=UW, pos=2,
         stem="对容器调用下面这行之后，里面的子部件会怎样？",
         code="""
m_box.hide();
// m_box 里有若干按钮，没有对它们单独调用 hide()""",
         right="随容器一并被隐藏，不必单独对它们调用 hide()",
         wrong=["仍然显示，因为 hide() 只作用于调用它的那一个部件",
                "被销毁，容器隐藏时会自动删除所有的子部件",
                "仍然显示，要对每个子部件分别调用 hide() 才会消失"],
         why="文档说明：对不想显示的部件调用 Gtk::Widget::hide() 可以将其隐藏；容器部件被隐藏时，它的所有子部件会一并被隐藏，即使没有在那些子部件上调用 hide()。",
         ref="使用 gtkmm 部件：hide() 隐藏容器时子部件一并被隐藏"),
    dict(id="rt30-uw-3", page=UW, pos=1,
         stem="部件作为指针成员声明时，本节说可以用什么来创建它？",
         right="new，或者 Gtk::make_managed()",
         wrong=["Glib::RefPtr 的 create()，部件同样是引用计数对象",
                "std::make_shared，部件要放进共享指针里管理",
                "指针成员不能用来持有部件，只能声明为普通成员"],
         why="本节的第一步：声明一个想使用的部件类型的变量，通常作为派生容器类的成员变量；也可以声明一个指向该部件类型的指针，然后在代码里用 new 或 Gtk::make_managed() 创建它。",
         ref="使用 gtkmm 部件：指针成员用 new 或 Gtk::make_managed() 创建"),
]

CHECKPOINT = [
    dict(id="rt30-cp-1", pos=2, locator="官方节页 sec-application-lifetime",
         stem="本节为什么建议让主窗口类继承 Window，而不是在 main() 里直接拼装部件？",
         right="子部件和信号处理函数都可成为该类的成员，代码更有条理",
         wrong=["只有继承 Window 才能连接信号，普通对象连不了",
                "继承之后窗口会被自动删除，不再需要 make_window_and_run()",
                "编译器要求每个窗口都有自己的类，否则链接失败"],
         why="文档说明：子类部件可以更好地组织代码，至少主窗口类应该继承 Window，这样就可以使主窗口的子部件和信号处理函数成为该类的成员。",
         ref="综合推荐技术：子类部件组织代码，主窗口类继承 Window"),
    dict(id="rt30-cp-2", pos=0, locator="官方节页 sec-application-lifetime",
         stem="下面哪种应用最适合直接使用 Gtk::Application::make_window_and_run()？",
         right="只有一个主窗口，关闭它就可以收尾的应用",
         wrong=["需要在同一进程里同时开多个互不相关的主窗口的应用",
                "不显示任何窗口，只在后台处理文件的命令行应用",
                "每次启动都要由程序员手动 delete 窗口的应用"],
         why="文档指出，大多数应用只有一个 Window 或只有一个主窗口，这样的应用可以使用 make_window_and_run()：它创建并显示窗口，窗口关闭时删除窗口并返回给调用者，本教程的大多数示例都用这种技术。",
         ref="综合推荐技术：只有一个主窗口的应用使用 make_window_and_run()"),
]

KP = dict(id="gtkmm.recommended.quizset", title="推荐技术测验集", difficulty=2, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-recommended-techniques", KP, inpage, cp)
        print("written")
