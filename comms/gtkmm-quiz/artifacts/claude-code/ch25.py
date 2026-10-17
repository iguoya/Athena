import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

SR, WD = "sec-memory-shared-resources", "sec-memory-widgets"

INPAGE = [
    dict(id="mm25-sr-1", page=SR, pos=1,
         stem="下面的代码里没有 new，也没有 delete，Pixbuf 是怎么释放的？",
         code="""
auto pixbuf = Gdk::Pixbuf::create_from_file(filename);""",
         right="pixbuf 是 RefPtr 智能指针，离开作用域时自动 unref",
         wrong=["Gdk::Pixbuf 是栈上对象，离开作用域时由析构函数直接释放",
                "gtkmm 带有垃圾回收器，会在程序空闲时定期扫描并回收",
                "create_from_file() 自己持有它，要到整个程序结束才释放"],
         why="Gdk::Pixbuf 这类来自共享存储的对象只能用 create() 之类的函数得到，返回的是 Glib::RefPtr<> 智能指针。pixbuf 离开作用域时 RefPtr 会在后台 unref，所以不用 delete，也没有 new。",
         ref="Reference counting and Glib::RefPtr：Pixbuf 只能用 create() 得到，RefPtr 离开作用域时自动 unref"),
    dict(id="mm25-sr-2", page=SR, pos=3,
         stem="pixbuf 先离开作用域、pixbuf2 还在使用时，这个 Pixbuf 实例会怎样？",
         code="""
auto pixbuf = Gdk::Pixbuf::create_from_file(filename);
auto pixbuf2 = pixbuf;   // 复制 RefPtr""",
         right="不会销毁，直到最后一个 RefPtr 离开作用域才销毁",
         wrong=["立即销毁，pixbuf2 随之变成指向已释放内存的悬空指针",
                "复制 RefPtr 时会深拷贝一个独立的 Pixbuf，两者互不影响",
                "引用只记在第一个 RefPtr 上，它离开作用域时实例就被释放"],
         why="复制 RefPtr（或把它作为方法参数、返回类型传递）时，RefPtr 会做必要的引用计数，确保实例在最后一个 RefPtr 离开作用域之前不会被销毁。复制的是指针，不是对象。",
         ref="Reference counting and Glib::RefPtr：复制 RefPtr 时自动引用，最后一个 RefPtr 离开作用域才销毁"),
    dict(id="mm25-sr-3", page=SR, pos=2,
         stem="下面两个智能指针是同一个类吗？",
         code="""
Glib::RefPtr<Gdk::Pixbuf> pixbuf;
Cairo::RefPtr<Cairo::Context> cr;""",
         right="不是：前者是 glibmm 的 RefPtr，后者是 Cairomm 自带的",
         wrong=["是同一个类，Cairo::RefPtr 只是 Glib::RefPtr 的别名",
                "不是：前者是 C++ 标准库的 shared_ptr，后者才是 RefPtr",
                "是同一个类，Cairomm 已改用 gtkmm 的 Glib::RefPtr"],
         why="gtkmm 对共享对象使用 Glib::RefPtr<> 智能指针，而 Cairomm 有自己的智能指针 Cairo::RefPtr<>。两者用法相似，但属于不同的库、不同的类型。",
         ref="Reference counting and Glib::RefPtr：Cairomm 有自己的智能指针 Cairo::RefPtr<>"),
    dict(id="mm25-wd-1", page=WD, pos=0,
         stem="下面类里的 theButton，什么时候销毁？需要手动 delete 吗？",
         code="""
class Foo : public Gtk::Window
{
private:
  Gtk::Button theButton;
  // will be destroyed when the Foo object is destroyed
};""",
         right="随 Foo 对象一起销毁，不需要手动 delete",
         wrong=["必须在 ~Foo() 里手动 delete，否则按钮会泄漏",
                "窗口一显示出来，按钮就被父窗口接管并删除",
                "离开构造函数时就销毁，所以按钮必须用 new 创建"],
         why="类作用域的部件是普通成员，随所属对象销毁而自动销毁，内存管理集中在一处，也不会因为忘记 delete 而泄漏。缺点是类头文件里暴露了实现细节而不是接口。",
         ref="Memory management of widgets：类作用域部件随所属对象一起销毁"),
    dict(id="mm25-wd-2", page=WD, pos=2,
         stem="如果删掉最后一行 delete pButton，会怎样？",
         code="""
auto pButton = new Gtk::Button("Test");
// do something useful with pButton
delete pButton;""",
         right="按钮从未加入任何父容器，没有别人会释放它，造成内存泄漏",
         wrong=["GTK 会在程序结束前扫描所有部件，自动补上这次 delete",
                "按钮在函数返回时，因 pButton 离开作用域而自动销毁",
                "程序会立刻崩溃，因为没有 delete 的 new 违反了 gtkmm 规则"],
         why="用 new 创建、又没有放进任何父容器的部件，释放它是程序员自己的责任。示例里的 delete pButton 正是为了防止内存泄漏。现代 C++ 风格不鼓励手写 new/delete，更好的做法是 make_managed()。",
         ref="Memory management of widgets：从未加入父容器的部件由程序员自己删除"),
    dict(id="mm25-wd-3", page=WD, pos=3,
         stem="下面的代码里，pButton 指向的按钮由谁负责释放？",
         code="""
MyContainer::MyContainer()
{
  auto pButton = Gtk::make_managed<Gtk::Button>("Test");
  append(*pButton); //add *pButton to MyContainer
}""",
         right="MyContainer：销毁它时会一并删除这个按钮，无需手动 delete",
         wrong=["构造函数结束时 pButton 离开作用域，按钮随之被销毁",
                "程序员必须在 ~MyContainer() 里手动 delete pButton",
                "Gtk::Application，在 run() 返回时统一释放所有 managed 部件"],
         why="用 Gtk::make_managed() 创建部件并 append() 进容器后，部件的生命周期委托给了容器：销毁 MyContainer 时按钮也被销毁，不需要再 delete pButton。",
         ref="Memory management of widgets：make_managed() 加 append()，由容器销毁子部件"),
    dict(id="mm25-wd-4", page=WD, pos=0,
         stem="gtkmm-4.0 里这样 delete 一个放在 Box 里的部件，会怎样？",
         code="""
auto b = new Gtk::Button("x");
m_Box.append(*b);
delete b;""",
         right="包装没了但 GtkWidget 仍在 Box 里；须先 m_Box.remove(*b)",
         wrong=["GtkWidget 随包装一起销毁，并自动从 Box 里移除掉",
                "delete 会抛异常，因为部件已经属于父容器，不能直接删除",
                "什么也不会发生，delete 对已加入容器的部件是个空操作"],
         why="gtkmm-4.0 与旧版本的重要区别：C++ 部件的析构不再导致放在父部件里的部件被销毁，此时 C 的 GtkWidget 仍然存活。依赖旧行为的代码，在 gtkmm-4.0 里必须先把部件从父部件中移除。",
         ref="Memory management of widgets：gtkmm-4.0 里析构放在父部件中的 C++ 部件不再销毁 GtkWidget"),
    dict(id="mm25-wd-5", page=WD, pos=1,
         stem="用 make_window_and_run() 创建的顶级窗口，窗口对象由谁删除？",
         code="""
return app->make_window_and_run<MyWindow>(argc, argv);""",
         right="窗口关闭时由它删除，程序员不必 delete",
         wrong=["程序员必须在 main() 里自己 delete，函数不会替你删窗口",
                "窗口是 main() 里的栈对象，在 main() 结束时由析构函数销毁",
                "由 Gtk::Application 的析构函数在退出时统一回收所有窗口"],
         why="顶级容器不会被加入另一个容器，通常由程序员用传统 C++ 手段销毁，或者让 Gtk::Application::make_window_and_run() 创建顶级窗口并在窗口关闭时删除它。",
         ref="Memory management of widgets：make_window_and_run() 创建顶级窗口并在关闭时删除"),
]

CHECKPOINT = [
    dict(id="mm25-cp-1", pos=1, locator="官方节页 sec-memory-widgets",
         stem="在构造函数里动态创建一个按钮并放进 Box，希望之后不用再操心销毁，哪种写法最符合本章的建议？",
         right="用 Gtk::make_managed 创建并 append，由容器销毁",
         wrong=["用 new 创建后 append，再在析构函数里 delete 掉它",
                "声明成构造函数里的局部变量，把它的地址 append 进 Box",
                "用 new 创建后既不放进容器，也不 delete，交给 GTK 回收"],
         why="make_managed() 把创建与标记合成一步：部件加入容器后，生命周期委托给容器，容器销毁时自动删除。局部变量在构造函数返回时就会销毁，容器里留下悬空指针；从未加入容器的 new 部件必须自己 delete。",
         ref="综合 Memory management of widgets：make_managed() 与容器接管部件生命周期"),
    dict(id="mm25-cp-2", pos=0, locator="官方节页 sec-memory-shared-resources 与 sec-memory-widgets",
         stem="下面三个对象里，哪一个需要你自己负责释放？",
         code="""
auto pixbuf = Gdk::Pixbuf::create_from_file(f);                    // A
auto b1 = Gtk::make_managed<Gtk::Button>("A"); m_Box.append(*b1);  // B
auto b2 = new Gtk::Button("B");                                    // C，从未加入任何容器""",
         right="只有 C：它是 new 出来的，又没有任何容器接管",
         wrong=["只有 A：Pixbuf 要自己调用 unref() 才能释放",
                "A 和 C：凡是函数返回的对象都要自己释放",
                "三个都要：gtkmm 的任何对象都需要显式释放"],
         why="A 是 RefPtr，离开作用域时自动 unref；B 用 make_managed() 并放进了 Box，由 Box 销毁；C 是 new 出来的部件且从未加入容器，释放它是你自己的责任。",
         ref="综合内存管理：RefPtr 自动 unref、managed 部件由容器销毁、new 且未加入容器要自己 delete"),
]

KP = dict(id="gtkmm.memory.quizset", title="内存管理测验集", difficulty=3, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-memory", KP, inpage, cp)
        print("written")
