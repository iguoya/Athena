import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))
from quizlib import build, report, apply

SE, HL, W, SIG, U, MIX, HW = (
    "sec-basics-simple-example", "sec-headers-and-linking", "sec-widgets-overview", "sec-signals-overview",
    "sec-basics-ustring", "sec-basics-gobj-and-wrap", "sec-helloworld")

INPAGE = [
    dict(id="basic3-se-1", page=SE, pos=1,
         stem="用户点击窗口的关闭按钮之后，下面的 main() 会怎样？",
         code="""
int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.examples.base");

  return app->make_window_and_run<MyWindow>(argc, argv);
}""",
         right="make_window_and_run() 返回，main() 随之返回，程序就此结束",
         wrong=["窗口只是隐藏，make_window_and_run() 仍在阻塞，程序继续运行",
                "窗口关闭后还得再调用 app->quit()，main() 才会返回，否则程序一直阻塞",
                "app 立刻被销毁，窗口类持有的资源因此泄漏，程序也无法正常退出"],
         why="make_window_and_run() 创建并显示窗口、进入 gtkmm 事件循环，窗口关闭时事件循环结束、函数返回，main() 跟着返回，不需要另外调用 quit()。",
         ref="Simple Example：最后一行创建并显示窗口，进入主循环，窗口关闭时结束"),
    dict(id="basic3-se-2", page=SE, pos=3,
         stem="main() 的第一行 Gtk::Application::create(\"org.gtkmm.examples.base\") 在程序里承担什么角色？",
         right="初始化 gtkmm，并得到 RefPtr 管理的 Application 对象",
         wrong=["创建 MyWindow 对象，并把它显示到屏幕上，然后等待用户操作",
                "进入事件循环，直到窗口被关闭才会返回，再把退出码交给 main()",
                "解析 argc/argv，并据此配置窗口的标题、大小和启动位置"],
         why="create() 初始化 gtkmm，返回存放在 Glib::RefPtr 里的 Application，所有 gtkmm 程序都需要它；创建窗口、进入事件循环是下一行 make_window_and_run() 的事。",
         ref="Simple Example：create() 初始化 gtkmm；窗口与主循环由 make_window_and_run() 负责"),
    dict(id="basic3-se-3", page=SE, pos=0, lang="bash",
         stem="下面这条编译命令在链接时会找不到 gtkmm 的符号，问题出在哪里？",
         code="""
g++ `pkg-config --cflags --libs gtkmm-4.0` base.cc -o base -std=c++17""",
         right="库参数要放在源文件之后，base.cc 应排在 pkg-config 前面",
         wrong=["-std=c++17 是必需选项，缺少它任何编译器都会拒绝编译",
                "反引号会把 pkg-config 当成普通文字，必须改成单引号",
                "gtkmm-4.0 不能交给 pkg-config 查询，只能手写库路径"],
         why="文档特别提醒：base.cc 必须写在 pkg-config 调用之前，链接器是按命令行顺序解析符号的。反引号是对的（让 shell 先执行命令再拼接输出）；-std=c++17 只有在编译器默认不支持 C++17 时才需要。",
         ref="Simple Example：编译命令及反引号、参数顺序说明"),
    dict(id="basic3-hl-1", page=HL, pos=2, lang="python",
         stem="执行下面这行 meson.build 代码时，实际发生了什么？",
         code="""
gtkmm_dep = dependency('gtkmm-4.0', version: '>= 4.6.0')""",
         right="检查系统里有没有够新的 gtkmm-4.0，并定义变量 gtkmm_dep",
         wrong=["自动下载 gtkmm 4.6.0 的源码，并编译到项目目录下",
                "把 gtkmm-4.0 的头文件复制进项目目录，供源码直接 include 使用",
                "生成 pkg-config 的 .pc 文件，并安装到系统目录"],
         why="dependency() 只检查 gtkmm 是否存在、版本是否够，并定义 gtkmm_dep；之后 executable() 的 dependencies 参数引用它，编译选项和链接库由它带上，不需要自己写 pkg-config。",
         ref="Headers and Linking：dependency() 检查 gtkmm 并定义 gtkmm_dep"),
    dict(id="basic3-hl-2", page=HL, pos=3,
         stem="gtkmm-2.4、gtkmm-3.0 与 gtkmm-4.0 能同时安装在同一台机器上，原因是？",
         right="API 名字不同，库名和头文件目录都分开，所以能并行安装",
         wrong=["三个版本共用同一份库文件，只是各自带的头文件不一样",
                "安装程序会把旧版本放进容器隔离，运行时才解包出来使用",
                "pkg-config 在运行时自动挑最新版，并把其他版本屏蔽掉"],
         why="API 名字（gtkmm-2.4 / 3.0 / 4.0）只在出现不兼容的 API 与 ABI 变化时才改，所以同一个 API 名下的多个小版本是互相替换的，而不同 API 名可以并行安装。",
         ref="Headers and Linking：gtkmm-4.0 是当前稳定 API 的名字，旧 API 并行安装"),
    dict(id="basic3-w-1", page=W, pos=1,
         stem="下面三行执行完之后，部件层级是怎样的？",
         code="""
m_box.append(m_Button1);
m_box.append(m_Button2);
m_frame.set_child(m_box);""",
         right="Frame 里装着 Box，Box 里依次是两个按钮",
         wrong=["Frame、Box 和两个按钮并列，都直接放在窗口里",
                "Box 里只剩 Button2，因为后一次 append() 会替换前一次",
                "Frame 里直接是两个按钮，不可见的 Box 在显示时被忽略掉"],
         why="部件一层套一层：append() 往 Box 末尾追加子部件，set_child() 把整个 Box 作为 Frame 的唯一子部件。Box 虽然不可见，只负责排列，但它仍然是层级里的一环。",
         ref="Widgets：部件放在容器里形成层级，Box 的 append() 与 Frame 的 set_child()"),
    dict(id="basic3-w-2", page=W, pos=2,
         stem="下面的代码里，按钮对象由谁负责释放？",
         code="""
auto& button = *Gtk::make_managed<Gtk::Button>("OK");
m_box.append(button);""",
         right="放进 m_box 后归 Box 所有，Box 销毁时自动删除，无需 delete",
         wrong=["程序员必须在 m_box 销毁之前，自己手动 delete 这个按钮",
                "append() 一返回，按钮就被引用计数释放，界面上看不到它",
                "由 Gtk::Application 对象在 main() 结束时统一回收销毁"],
         why="Gtk::make_managed() 创建的部件一旦放进容器，就归容器所有，容器销毁时自动删除它，所以不用再操心释放，这是文档提到的省事用法。",
         ref="Widgets：Gtk::make_managed() 让部件归其所放入的容器所有"),
    dict(id="basic3-sig-1", page=SIG, pos=0,
         stem="下面这行 connect() 执行的那一刻，on_button_clicked() 会被调用吗？",
         code="""
m_button1.signal_clicked().connect( sigc::mem_fun(*this,
  &HelloWorld::on_button_clicked) );""",
         right="不会。connect() 只登记，按钮每发出一次 clicked 才调用一次",
         wrong=["会。connect() 先调用一次，用来检查处理函数的签名是否匹配",
                "会。连接成功时立刻先调用一次，之后每次点击再各调用一次",
                "不会。处理函数只在窗口关闭前被调用一次，不随点击重复"],
         why="connect() 把处理函数登记到信号上，本身不调用它；之后每当按钮发出 clicked 信号，登记过的处理函数就被调用一次。信号是事件驱动的：先登记，事件发生时才执行。",
         ref="Signals：把 clicked 信号连接到 on_button_clicked 的示例"),
    dict(id="basic3-sig-2", page=SIG, pos=1,
         stem="用户按下一个按钮时，clicked 信号是由谁发出的？",
         right="被按下的那个部件（Gtk::Button）自己",
         wrong=["Gtk::Application 对象，再统一转发给各个窗口",
                "按钮所在的窗口类，如 HelloWorld",
                "操作系统直接调用你登记的处理函数"],
         why="gtkmm 是事件驱动的：事件发生时，对应的部件发出自己的信号，每种部件能发出的信号集合不同。要让点击产生动作，就给那个部件的信号连接处理函数。",
         ref="Signals：事件发生时由被按下的部件发出相应信号"),
    dict(id="basic3-u-1", page=U, pos=3,
         stem="假设源文件按 UTF-8 保存，下面的 head 是什么？",
         code="""
Glib::ustring s = "你好，gtkmm";
auto head = s.substr(0, 2);""",
         right="“你好”，substr() 按字符计数，而不是按字节",
         wrong=["“你”，因为每个汉字占 2 字节，2 个字节只够一个字",
                "“你好，”，因为第二个参数表示结束位置而不是长度",
                "一个残缺的字符，UTF-8 汉字占 3 字节，被从中间截断了"],
         why="Glib::ustring 帮你处理 UTF-8 的细节，substr() 之类的方法以字符为单位，所以取前 2 个字符就是“你好”。若用 std::string，同样的调用按字节算，会把汉字截断。",
         ref="Glib::ustring：substr() 以字符而不是字节思考"),
    dict(id="basic3-u-2", page=U, pos=2,
         stem="下面的 n 是多少？为什么本章建议避免 strlen() 这类函数？",
         code="""
Glib::ustring text = "你好";
auto n = strlen(text.c_str());""",
         right="6。strlen() 数字节而不是字符，UTF-8 字符长度并不固定",
         wrong=["2。strlen() 能识别 UTF-8，按字符边界计数",
                "2。Glib::ustring 重载了 strlen()，让它按字符来计数",
                "编译失败。Glib::ustring 没有提供 c_str() 这个方法"],
         why="UTF-8 里每个字符可能占 1~6 个字节（常见汉字 3 个字节），所以 strlen() 得到 6 而不是 2。指针算术和 strlen() 会数错字符，应当使用 Glib::ustring 的方法，如 length() 与 substr()。",
         ref="Glib::ustring：避免 C 风格指针算术和 strlen()，UTF-8 字符占 1~6 字节"),
    dict(id="basic3-mix-1", page=MIX, pos=0,
         stem="执行 Glib::wrap(cbutton) 之后，关于 C 对象的生命周期，哪项说法正确？",
         code="""
GtkButton* cbutton = get_a_button();
Gtk::Button* button = Glib::wrap(cbutton);
button->set_label("Now I speak C++ too!");""",
         right="引用计数不增加；包装与 C 实例绑定，别在要用 C 实例时删包装",
         wrong=["引用计数加 1；删除包装对象之后，C 实例仍然保持存活不变",
                "wrap() 会深拷贝出一个独立的 C 对象，原对象完全不受影响",
                "包装对象永远由 RefPtr 自动管理，从来不需要手动 delete"],
         why="Glib::wrap() 把 C 实例和 C++ 包装绑在一起，默认不增加引用计数（take_copy 为 true 才增加）。部件类等某些情形下包装必须显式 delete，所以不要在还要 C 实例活着的时候删除包装对象。",
         ref="Mixing C and C++ APIs：Glib::wrap() 绑定两个实例，默认不增加引用计数"),
    dict(id="basic3-mix-2", page=MIX, pos=1,
         stem="要把 gtkmm 对象交给只认 C GObject 的函数，空白处该写什么？",
         code="""
Gtk::Button button("example");
gtk_button_do_something_that_gtkmm_cannot(____);""",
         right="button.gobj()，取得底层 C 实例的指针",
         wrong=["Glib::wrap(button)，把它包装成 C 对象",
                "button.c_obj()，返回 C 版本的按钮",
                "(GtkButton*)button，直接强制类型转换"],
         why="gobj() 返回 gtkmm 对象背后的 C 实例指针；方向相反（从 C 实例得到 C++ 对象）才用 Glib::wrap()。C++ 包装类不能靠强制转换变成 C 指针。",
         ref="Mixing C and C++ APIs：用 gobj() 取得底层 C 实例"),
    dict(id="basic3-hw-1", page=HW, pos=2,
         stem="如果删掉构造函数里的 set_child(m_button)，运行 Hello World 会看到什么？",
         code="""
HelloWorld::HelloWorld()
: m_button("Hello World")
{
  m_button.set_margin(10);
  m_button.signal_clicked().connect(sigc::mem_fun(*this,
    &HelloWorld::on_button_clicked));
  set_child(m_button);   // ← 删掉这一行
}""",
         right="窗口能打开但里面是空的，按钮没有放进窗口，也就点不到",
         wrong=["编译失败，Gtk::Window 必须设置了子部件才能构造",
                "按钮照样出现在窗口里，成员变量会自动成为子部件",
                "窗口一打开就崩溃，因为 m_button 没有父部件"],
         why="成员变量只是创建了按钮对象，要让它出现在窗口里，必须用 set_child() 把它放进去。没有这一步，窗口是空的，按钮即使连了信号也不会被点到。",
         ref="Hello World：set_child() 把按钮放进窗口"),
    dict(id="basic3-hw-2", page=HW, pos=3,
         stem="main.cc 里没有出现 HelloWorld 类型的变量，窗口对象是谁、什么时候创建的？",
         code="""
auto app = Gtk::Application::create("org.gtkmm.example");
return app->make_window_and_run<HelloWorld>(argc, argv);""",
         right="make_window_and_run<HelloWorld>() 运行时创建并显示它",
         wrong=["Gtk::Application::create() 在初始化时顺便创建了它",
                "它是全局对象，在 main() 开始之前就已经创建好了",
                "窗口关闭之后才创建，用来保存用户所做的修改内容"],
         why="make_window_and_run<HelloWorld>() 创建 HelloWorld 对象、显示窗口并启动事件循环；窗口关闭后函数返回，main() 随之结束。窗口类的构造函数里完成布置部件与连接信号的初始化。",
         ref="Hello World：make_window_and_run() 创建窗口对象、显示并启动事件循环"),
]

CHECKPOINT = [
    dict(id="basic3-cp-1", pos=0, locator="官方节页 sec-basics-simple-example 与 sec-helloworld",
         stem="下面的程序编译通过，运行后会怎样？",
         code="""
int main(int argc, char* argv[])
{
  auto app = Gtk::Application::create("org.gtkmm.demo");
  MyWindow win;
  return 0;
}""",
         right="立刻退出，窗口没机会显示，因为没有进入事件循环",
         wrong=["窗口显示出来，直到用户关闭才退出",
                "窗口一闪而过，随后 return 0 把它关掉",
                "窗口显示出来，但点击按钮没有任何响应"],
         why="窗口要显示并响应事件，必须进入 gtkmm 事件循环，这正是 make_window_and_run() 做的事（创建窗口、显示、启动事件循环）。这段代码只构造了对象就返回，程序立即结束。",
         ref="综合 Simple Example 与 Hello World：创建 Application → make_window_and_run()"),
    dict(id="basic3-cp-2", pos=2, locator="官方节页 sec-basics-ustring",
         stem="程序要按字符截取用户输入的中文，该怎么做？",
         right="用 std::string 存储，再用 substr() 按字节截取",
         wrong=["用 std::string 存储，再用 substr() 按字节截取",
                "按 GBK 转码后再计算字节数",
                "避免使用任何字符串，只处理数字"],
         why="", ref=""),
    dict(id="basic3-cp-3", pos=1, locator="官方节页 sec-widgets-overview",
         stem="需要动态创建一个按钮放进 m_box，哪种做法最符合本章的建议？",
         right="用 Gtk::make_managed 创建并 append，按钮随容器一起销毁",
         wrong=["用 new 创建后立刻 delete 掉它，这样部件才能显示出来",
                "声明成成员变量，再用 gobj() 把所有权交给 C 代码管理",
                "用 Glib::wrap() 去包装一个新建的 C 对象，再手动 unref"],
         why="Gtk::make_managed() 创建的部件放进容器后归容器所有，容器销毁时自动删除，不用手写 delete。立刻 delete 会让部件消失，gobj() 与 wrap() 解决的是 C 与 C++ 互操作，不是常规的生命周期管理。",
         ref="综合 Widgets：Gtk::make_managed() 与容器所有权"),
]

# 第 2 题改成不再自相矛盾的正确写法
CHECKPOINT[1].update(
    right="用 Glib::ustring 存储，并用 substr() 等方法按字符处理",
    wrong=["用 std::string 存储，再用 substr() 按字节截取",
           "先转成 GBK 编码，再按每两个字节算一个字符来处理",
           "用 strlen() 求长度，再用指针算术逐字节往后移动指针"],
    why="gtkmm 的接口使用 Glib::ustring，它按 UTF-8 字符而不是字节处理文本；std::string、strlen() 与指针算术按字节计数，遇到中文会数错、截断字符。",
    ref="综合 Glib::ustring：多语言文本按字符处理，避免 strlen() 与指针算术",
)

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply("chapter-basics", 0, inpage, cp)
        print("written")
