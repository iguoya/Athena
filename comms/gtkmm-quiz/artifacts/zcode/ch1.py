"""第 1 章（chapter-introduction）测验标准版草稿：sec-this-book / sec-gtkmm / sec-cpp-resources。

sec-cpp-resources 只是一份 C++ 资源链接清单（旧题 intro-cpp-1 是背链接的弱题），本稿删去，
不再为它凑题。全部事实锚定本章快照英文原文。
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

TB, GTK = "sec-this-book", "sec-gtkmm"

INPAGE = [
    dict(id="intro-tb-1", page=TB, pos=1,
         stem="关于这本书讲解 gtkmm 的方式，哪项说法与本章前言一致？",
         right="讲关键概念与主要部件，完整 API 查参考文档",
         wrong=["逐类讲解每个类的完整 API，读完不必再查参考文档",
                "从 C++ 语言基础讲起，适合还没写过 C++ 程序的读者",
                "只讲界面设计理念，不涉及类、构造函数这些具体细节"],
         why="本书解释 gtkmm C++ API 的关键概念、介绍主要部件，会提到类、构造函数与方法但不深入细节，完整 API 信息要顺着链接进参考文档；同时本书假定读者已有良好的 C++ 基础，不从语言教起。",
         ref="sec-this-book 第 1 段：关键概念 + 参考文档链接；第 2 段：假定已懂 C++"),
    dict(id="intro-gtk-1", page=GTK, pos=2,
         stem="公司打算用 gtkmm 开发一款闭源的商业软件，LGPL 许可下可以吗？",
         right="可以：LGPL 下商业非自由软件也能开发，无需购买授权",
         wrong=["不可以：用 gtkmm 写的软件必须开源，否则构成侵权",
                "可以，但要先向 GTK 项目购买一份商业开发许可",
                "不可以：gtkmm 只许可用于自由软件，商业用途未获授权"],
         why="原文：gtkmm 以 LGPL 许可发布，因此可以开发开放软件、自由软件乃至商业非自由软件（commercial non-free software），不用购买许可。「LGPL 等于必须开源」是把 GPL 的强传染要求错套到 LGPL 上。",
         ref="sec-gtkmm 第 1 段：LGPL；open / free / commercial non-free 均可"),
    dict(id="intro-gtk-2", page=GTK, pos=0,
         stem="对照下面两种创建按钮的写法，本章说 gtkmm 这一侧的好处是？",
         code="""
// GTK（C API）
GtkWidget* button = gtk_button_new_with_label("OK");
// gtkmm
Gtk::Button m_button("OK");""",
         right="部件可用成员实例，内存管理更简单",
         wrong=["完全不用关心生命周期，gtkmm 部件永不销毁",
                "成员实例比指针执行更快，C API 因此性能差",
                "C API 其实也能用成员实例，差别只在命名风格"],
         why="原文：GTK C 的部件全部靠指针处理；gtkmm 允许把部件用作成员实例，从而简化内存管理，而 C++ 程序员本就应尽量少用指针。说的是管理更简单，不是「零生命周期」，也没有性能高低的说法。",
         ref="sec-gtkmm why use gtkmm 列表：member instances / pointers 一条"),
    dict(id="intro-gtk-3", page=GTK, pos=3,
         stem="本章比较 gtkmm 与 Qt 时，说两者实现「信号」的方式差在哪？",
         right="gtkmm 用标准 C++ 提供信号，没有改语言",
         wrong=["gtkmm 靠预处理宏生成信号，Qt 用的是编译器扩展",
                "两家都修改了 C++ 语言，只是引入的关键字不一样",
                "两家都没改语言，信号机制只是普通虚函数调用"],
         why="原文：Trolltech 为了提供信号修改了 C++ 语言本身，导致 Qt 类难以与非 Qt 类配合使用；gtkmm 不改语言，用标准 C++ 就实现了信号。误解方向是把信号当成语言魔法或普通虚函数，而 gtkmm 的做法恰恰是「不特殊」。",
         ref="sec-gtkmm gtkmm compared to Qt 末段：modified the C++ language / standard C++"),
]

CHECKPOINT = [
    dict(id="intro-cp-1", pos=1, locator="官方节页 sec-gtkmm",
         stem="想在程序里定制按钮的行为。关于「派生自己的部件」，本章怎么说 gtkmm 与 GTK C 的差别？",
         code="""
class MyButton : public Gtk::Button {
public:
  void do_something();  // 定制行为
};""",
         right="gtkmm 里是常规继承；GTK C 里复杂易错，几乎没人做",
         wrong=["两边都很常见，GTK C 里派生新部件同样是日常操作",
                "gtkmm 不允许继承内置部件，只能通过组合来定制",
                "派生出的部件无法放进容器，界面上显示不出来"],
         why="原文：继承可用来派生新部件；而在 GTK C 代码里派生新部件如此复杂易错，几乎没有 C 程序员这么做，但派生正是 C++ 程序员的基本面向对象手法。gtkmm 没有禁止继承内置部件。",
         ref="综合 sec-gtkmm why use gtkmm 列表：inheritance / derive new widgets 一条"),
    dict(id="intro-cp-2", pos=2, locator="官方节页 sec-gtkmm",
         stem="「gtkmm 不是原生 C++ 工具集，而是 C 工具集的 C++ 包装」。按本章，接口与实现的分离带来什么好处？",
         right="gtkmm 呈现清晰 API；GTK 多语言共享生态",
         wrong=["省去了重复劳动，gtkmm 不必跟随 GTK 的发布节奏",
                "降低了学习门槛，C 程序员能直接读懂 gtkmm 代码",
                "属于历史包袱，gtkmm 终将重写为原生 C++ 工具集"],
         why="原文说这种分离有好处：gtkmm 开发者把大部分时间花在如何呈现最清晰的 API 上，不为晦涩的技术细节妥协；GTK 则享有比语言专属工具集更广的用户基础——实现者、开发者、测试者、用户都更多。分离不是为了让 gtkmm 脱离 GTK 独立演进。",
         ref="综合 sec-gtkmm gtkmm is a wrapper 一节"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
