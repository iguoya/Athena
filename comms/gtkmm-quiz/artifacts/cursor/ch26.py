import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

LD, AC, DW = (
    "sec-builder-loading-ui-file",
    "sec-builder-accessing-widgets",
    "sec-builder-using-derived-widgets",
)

INPAGE = [
    dict(id="bd26-ld-1", page=LD, pos=1,
         stem="做 gtkmm4 界面布局时，为什么本章推荐 Cambalache 而不是 Glade？",
         right="Cambalache 取代 Glade，后者不支持 gtk4",
         wrong=["Glade 仍是官方首选，Cambalache 只是可选的第三方皮肤工具",
                "二者都能导出 gtk4 的 .ui，只是 Cambalache 换了文件后缀",
                "Glade 能直接生成 C++ 源码，所以 Builder 章根本用不到它"],
         why="原文明确：Cambalache replaces the Glade application。Glade 可生成给 gtk3/gtkmm3 用的 XML，但不支持 gtk4/gtkmm4。界面仍是 .ui XML，运行时用 Gtk::Builder 加载。",
         ref="Loading the .ui file：Cambalache 取代 Glade；Glade 不支持 gtk4"),
    dict(id="bd26-ld-2", page=LD, pos=0,
         stem="下面两行分别会实例化 .ui 里的哪些对象？",
         code="""
auto all = Gtk::Builder::create_from_file("basic.ui");
auto one = Gtk::Builder::create_from_file("basic.ui", "treeview_products");""",
         right="all 建窗口；one 只建 treeview_products 这一个",
         wrong=["两行效果相同：第二参数只是给 Builder 起的调试别名而已",
                "one 会先实例化全部窗口，再把无关窗口立刻 delete 掉",
                "all 什么都不建，要等 get_widget() 才会真正构造部件"],
         why="原文：create_from_file(\"basic.ui\") 会实例化文件里定义的窗口；若只想要其中一个窗口或某个子部件，把部件名作为第二参数。部件在 create_from_file / add_from_file 期间就已经实例化，不是等到 get_widget。",
         ref="Loading the .ui file：create_from_file 与可选的第二参数（部件名）"),
    dict(id="bd26-ac-1", page=AC, pos=2,
         stem="连续两次 get_widget 同一名字，得到的指针关系是？",
         code="""
auto a = builder->get_widget<Gtk::Window>("DialogBasic");
auto b = builder->get_widget<Gtk::Window>("DialogBasic");""",
         right="a、b 指向同一实例：get_widget 只取指针",
         wrong=["每次都会新建窗口，所以 a 与 b 地址不同、内容却相同",
                "第二次返回 nullptr，同名只能取一次以免重复拥有",
                "编译失败：get_widget 规定每个名字至多只能调用一次"],
         why="原文：get_widget() 并不是在实例化部件，只是取得已存在实例的指针；同一 Builder、同一名字总是得到同一实例。实例化发生在 create_from_file()（或 add_from_file）期间。找不到或类型不对则指针为 nullptr。",
         ref="Accessing widgets：get_widget 取已有实例；同名总是同一指针"),
    dict(id="bd26-ac-2", page=AC, pos=3,
         stem="本章示例把「对话框」写成派生自谁？原因是什么？",
         code="""
auto pDialog = builder->get_widget<Gtk::Window>("DialogBasic");""",
         right="Gtk::Window：Gtk::Dialog 自 4.10 起已弃用",
         wrong=["Gtk::Dialog：本章示例仍把 Dialog 当作官方推荐基类",
                "Gtk::Application：对话框必须直接就是 Application 本身",
                "Gtk::Box：无父容器的顶层窗应改成可 manage 的子部件"],
         why="原文专句：本章对话框派生自 Gtk::Window，因为 Gtk::Dialog 自 gtkmm 4.10 起已弃用。示例变量名仍叫 pDialog，模板参数却是 Gtk::Window。",
         ref="Accessing widgets：Dialog 弃用，改用 Window"),
    dict(id="bd26-dw-1", page=DW, pos=1,
         stem="要让 get_widget_derived 构出 DerivedDialog，构造函数至少要满足什么？",
         code="""
DerivedDialog::DerivedDialog(BaseObjectType* cobject,
  const Glib::RefPtr<Gtk::Builder>& builder)
: Gtk::Window(cobject)
{
}""",
         right="收 C 指针与 Builder；初始化列表交给基类",
         wrong=["只接收 Builder，靠基类默认构造去包装那个底层 C 对象",
                "只接收 cobject，Builder 得改成全局变量再去取子部件",
                "随便收三个类型参数即可，只要名字对上就会自动绑定"],
         why="原文：派生类必须有接收底层 C 类型指针与 Gtk::Builder 的构造函数；相关 gtkmm 类把底层 C 类型 typedef 为 BaseObjectType。必须在初始化列表调用基类构造并传入该 C 指针。额外参数可以再从 get_widget_derived 往后传。",
         ref="Using derived widgets：构造函数签名与基类初始化"),
    dict(id="bd26-dw-2", page=DW, pos=0,
         stem="带 Glib::Property 成员的 DerivedButton，为何要在 add_from_file 之前先造一个哑元实例？",
         code="""
static_cast<void>(DerivedButton());
refBuilder->add_from_file("derived.ui");""",
         right="先注册 GType：含 Property 的类须在 add_from_* 前注册",
         wrong=["用来预热缓存，否则 add_from_file 会把整个 .ui 解析两遍",
                "哑元实例会留在界面上，当作 Builder 找不到部件时的后备",
                "只有这样 Builder 才允许对普通 Gtk::Button 调用 get_widget"],
         why="原文：含 Glib::Property 的派生部件必须以自己的名字注册到 GType，且须在任何 create_from_* / add_from_* 之前注册——因此可能要先专门建一个实例完成注册。构造函数里还要调 Glib::ObjectBase(\"MyButton\") 注册类型。",
         ref="Gtk::Builder and Glib::Property：GType 注册须早于 add_from_*"),
]

CHECKPOINT = [
    dict(id="bd26-cp-1", pos=2, locator="官方节页 sec-builder-accessing-widgets",
         stem="从 Builder 取出的顶层 Window，生命周期上要注意什么？",
         right="Window 不能 manage：无父容器，须在合适时机自行 delete",
         wrong=["和子部件一样已被 manage()，父容器销毁时会自动删掉",
                "归 Gtk::Application 永久持有，退出前绝对不能 delete",
                "get_widget 返回值类型，离开作用域就析构，不用再管"],
         why="原文：get_widget() 返回的子部件是 manage() 过的，随父容器删除；Window（含旧称 Dialog）没有父容器，不能 manage，必须在某处自行删除。basic 示例在 signal_window_removed 里 delete window，并提醒 run() 返回后再删已经来不及。",
         ref="综合 Accessing widgets：子部件 manage vs Window 需手动删除"),
    dict(id="bd26-cp-2", pos=3, locator="官方节页 sec-builder-using-derived-widgets",
         stem="get_widget_derived 多传一个 true，会落到哪个构造函数？",
         code="""
pDialog = Gtk::Builder::get_widget_derived<DerivedDialog>(
    refBuilder, "DialogDerived", true);""",
         right="三参数版：true 作为额外的 bool 传入",
         wrong=["两参数版：多余的 true 被静默丢掉，行为与完全不传相同",
                "默认构造：Builder 改走 DerivedDialog()，再手工去 wrap",
                "编译失败：get_widget_derived 不允许在名字后面再跟参数"],
         why="原文：可以把额外实参从 get_widget_derived() 传给派生部件构造函数；示例 (... , true) 对应 DerivedDialog(cobject, builder, bool warning/is_glad)。前两个参数在会从 get_widget_derived 调用的构造函数里是必填的。",
         ref="综合 Using derived widgets：额外实参转发到派生构造函数"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
