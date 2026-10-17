import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

TR, PW, OF, MN, PD, PR, HB = ("sec-buildapp-trivial-app", "sec-buildapp-populating-window", "sec-buildapp-opening-files",
                              "sec-buildapp-menu", "sec-buildapp-pref-dialog", "sec-buildapp-properties",
                              "sec-buildapp-header-bar")

INPAGE = [
    dict(id="ba31-tr-1", page=TR, pos=1,
         stem="用 HANDLES_OPEN 标志创建的应用，带文件名和不带参数启动时，各会调用哪个处理函数？",
         code="""
ExampleApplication::ExampleApplication()
: Gtk::Application("org.gtkmm.examples.application", Gio::Application::Flags::HANDLES_OPEN)
{ ... }

void on_activate() override;
void on_open(const Gio::Application::type_vec_files& files, const Glib::ustring& hint) override;""",
         right="带文件参数调用 on_open()，不带参数调用 on_activate()",
         wrong=["不管带不带参数，都只调用 on_activate()，文件另外处理",
                "带文件参数调用 on_activate()，不带参数调用 on_open()",
                "两个都调用：先 on_open() 处理文件，再 on_activate() 开窗口"],
         why="为处理这两种情况，示例覆写了 signal_activate() 的默认处理函数（没有命令行参数时调用）和 signal_open() 的默认处理函数（带命令行参数启动时调用）。创建应用时的 HANDLES_OPEN 标志让它接受文件参数。",
         ref="构建应用程序：覆写 on_activate() 与 on_open() 的默认处理函数，HANDLES_OPEN 标志"),
    dict(id="ba31-tr-2", page=TR, pos=3,
         stem="下面的 main() 里，application->run() 什么时候返回？",
         code="""
int main(int argc, char* argv[])
{
  auto application = ExampleApplication::create();
  // Start the application, showing the initial window,
  // and opening extra views for any files that it is asked to open,
  // for instance as a command-line parameter.
  // run() will return when the last window has been closed.
  return application->run(argc, argv);
}""",
         right="最后一个窗口关闭时返回",
         wrong=["显示初始窗口之后立即返回，窗口由事件循环另行维持",
                "第一个窗口关闭时返回，其余窗口随之销毁",
                "所有命令行文件都打开完毕时返回，窗口在其后显示"],
         why="示例注释写明：run() 在最后一个窗口关闭时返回。使用 Gtk::Application 时 main() 可以很简单，只需在应用类实例上调用 run()，应用的逻辑都在应用类里。",
         ref="构建应用程序：main() 只调用 run()，在最后一个窗口关闭时返回"),
    dict(id="ba31-tr-3", page=TR, pos=0,
         stem="应用类构造函数里的这一行起什么作用？",
         code="""
// Delete a window when it is removed from the application.
signal_window_removed().connect([](Gtk::Window* window) { delete window; });""",
         right="窗口被移除时，delete 这个窗口",
         wrong=["阻止窗口被移除，让应用始终保留所有窗口",
                "窗口一被移除就让整个应用立刻退出",
                "每次创建新窗口时，自动把旧窗口移除并 delete"],
         why="应用持有的窗口由程序员负责删除。示例连接 signal_window_removed()，在窗口从应用中移除时 delete 它，这是顶级窗口不被加入别的容器时常用的释放方式之一。",
         ref="构建应用程序：signal_window_removed() 里 delete 窗口（示例注释）"),
    dict(id="ba31-pw-1", page=PW, pos=2,
         stem="下面这条命令做了什么？代码里为什么读 ui 文件要用 _from_resource() 变体？",
         lang="bash",
         code="""
$ glib-compile-resources --target=resources.c --generate-source exampleapp.gresource.xml""",
         right="生成 resources.c，把 ui 编进二进制",
         wrong=["把 ui 文件复制到 /usr/share，运行时再按路径去读取",
                "检查 gresource.xml 的语法，通过后不生成任何文件",
                "生成一个新的 ui 文件，用来取代原来的 window.ui"],
         why="使用 GLib 的资源功能把 ui 文件包含进二进制：把所有资源列在 .gresource.xml 里，用 glib-compile-resources 转成一个 C 源文件，与其他源文件一起编译并链接进应用程序。所以读取时用 Builder 的 _from_resource() 变体。",
         ref="构建应用程序：glib-compile-resources 把资源编译成 C 源文件并链接进应用"),
    dict(id="ba31-of-1", page=OF, pos=0,
         stem="如果 window.ui 里没有 id 为 stack 的对象，窗口构造时会怎样？",
         code="""
m_stack = m_refBuilder->get_widget<Gtk::Stack>("stack");
if (!m_stack)
  throw std::runtime_error("No \\"stack\\" object in window.ui");""",
         right="返回 nullptr，构造函数抛出异常",
         wrong=["get_widget() 会新建一个 Gtk::Stack，所以不会进入 if 分支",
                "编译失败，Builder 要求所有 id 在编译时都已知",
                "程序继续运行，m_stack 悬空，直到第一次使用才崩溃"],
         why="get_widget() 不会实例化部件，只是取得已存在部件的指针；找不到该名字的部件时指针为 nullptr，示例据此抛出异常，及早暴露 window.ui 与代码不一致的问题。",
         ref="构建应用程序：在构造函数里用 Gtk::Builder::get_widget() 取得 Gtk::Stack 指针并检查"),
    dict(id="ba31-mn-1", page=MN, pos=1,
         stem="为什么示例建议在 on_startup() 的默认处理函数里添加应用级动作？",
         right="它保证对每个主应用实例只调用一次",
         wrong=["它在每次 on_activate() 之前调用，所以每开一个窗口都重新添加",
                "它在窗口创建之后调用，所以动作可以直接绑定到窗口上",
                "只有 on_startup() 才能访问菜单模型，别处拿不到 Builder"],
         why="菜单通过激活 Gio::Action 工作，所以要给应用添加一组合适的动作。文档建议在 on_startup() 里添加，因为它保证每个主应用实例只调用一次；快捷键（如 Ctrl-Q）用 Gtk::Application::set_accel_for_action() 添加。",
         ref="构建应用程序：在 on_startup() 里添加动作，保证每个主应用实例只调用一次"),
    dict(id="ba31-pd-1", page=PD, pos=3,
         stem="用下面的代码绑定之后，用 gsettings 命令行工具改了 transition 设置，会怎样？",
         code="""
m_settings = Gio::Settings::create("org.gtkmm.exampleapp");
m_settings->bind("transition", m_stack->property_transition_type());""",
         right="应用立刻响应，属性随设置变化",
         wrong=["没有反应，必须重启应用，新的设置才会生效",
                "没有反应，要自己连接 signal_changed() 才能读到新值",
                "只在下一次调用 open_file_view() 时才会读取新设置"],
         why="Gio::Settings::bind() 把设置键与对象属性绑定起来，之后设置一变，属性就跟着变。文档说，即使还没有首选项对话框，只要改动其中一项设置（例如用 gsettings 命令行工具），应用就会做出反应。",
         ref="构建应用程序：用 Gio::Settings::bind() 绑定设置键与对象属性"),
    dict(id="ba31-pd-2", page=PD, pos=2,
         stem="使用 Gio::Settings 之前，必须先具备什么？",
         right="描述设置的 schema（.gschema.xml），并编译成二进制形式",
         wrong=["只要调用 Gio::Settings::create()，键会在第一次写入时自动创建",
                "一个 .ui 文件，其中列出所有设置键和默认值",
                "一份 .gresource.xml，把设置项登记为应用的资源"],
         why="Gio::Settings 需要一个描述设置的 schema，本例是 org.gtkmm.exampleapp.gschema.xml；在应用中使用前要把它编译成 Gio::Settings 期望的二进制形式（autotools 有对应的宏，Meson 在 GNOME 模块里提供 compile_schemas()）。",
         ref="构建应用程序：Gio::Settings 需要 schema，并编译成二进制形式"),
    dict(id="ba31-pr-1", page=PR, pos=1,
         stem="每次激活 show-lines 动作，会发生什么？",
         code="""
add_action(Gio::PropertyAction::create("show-lines", m_lines->property_visible()));
m_binding_lines_visible = Glib::Binding::bind_property(m_lines->property_visible(),
  m_lines_label->property_visible());""",
         right="lines 标签切换，lines_label 同步",
         wrong=["只有 lines 标签被切换，lines_label 不受影响",
                "动作每次被激活都会新建一个标签，旧标签被销毁",
                "没有可见变化，两个属性只是在内部互相复制一个初值"],
         why="属性动作把 lines 标签的 visible 属性包装成动作，每次激活都切换它的可见性；Glib::Binding 又把 lines_label 的 visible 绑定到同一个属性上，所以两个标签总是一起出现、一起消失。",
         ref="构建应用程序：Gio::PropertyAction 包装属性，Glib::Binding 绑定两个属性"),
    dict(id="ba31-hb-1", page=HB, pos=0,
         stem="window.ui 里这样设置之后，标题栏会显示哪些按钮？",
         lang="xml",
         code="""
<object class="GtkHeaderBar" id="header">
  <property name="decoration-layout">icon:close</property>""",
         right="只有窗口图标和关闭按钮，最小化与最大化被隐藏",
         wrong=["只有最小化和最大化按钮，关闭按钮被隐藏",
                "三个按钮都显示，icon:close 只影响它们的顺序",
                "什么按钮也不显示，只剩下窗口标题的文字部分"],
         why="decoration-layout 属性在 window.ui 里设为 icon:close，使标题栏只显示关闭按钮（以及图标），隐藏最小化与最大化按钮。示例还在资源文件里包含一个图标，并把它设为窗口图标。",
         ref="构建应用程序：HeaderBar 的 decoration-layout 属性，只显示关闭按钮"),
]

CHECKPOINT = [
    dict(id="ba31-cp-1", pos=2, locator="官方节页 sec-buildapp-trivial-app 与 sec-buildapp-populating-window",
         stem="本章为什么建议把 ui 文件放进二进制里，而不是安装到 /usr/share 下的特定位置？",
         right="免去了大多数要装进 /usr/share 的应用专属文件",
         wrong=["资源比磁盘文件更安全，用户无法修改其中的内容",
                "Gtk::Builder 只支持 create_from_resource()，读不了文件",
                "这样 ui 文件可以在运行时被程序改写并保存"],
         why="像 Gtk::Builder 的 ui 文件这样的其他文件，最好从应用程序二进制本身存储的资源里加载。这样就不需要按传统把大多数文件安装到 /usr/share 中特定应用程序的位置。桌面文件、图标和 schema 仍要安装到各自的位置。",
         ref="综合构建应用程序：ui 文件最好从资源加载，免去安装到 /usr/share 的需要"),
    dict(id="ba31-cp-2", page=None, pos=3, locator="官方节页 sec-buildapp-pref-dialog",
         stem="为什么连接字体设置要先 create_tag()？",
         code="""
auto tag = buffer->create_tag();
m_settings->bind("font", tag->property_font());
buffer->apply_tag(tag, buffer->begin(), buffer->end());""",
         right="绑定目标是 TextTag 的 font 属性",
         wrong=["TextBuffer 自己没有字体概念，所以必须用 tag 代替它存字体",
                "只有 tag 才能连接 Gio::Settings，其他对象都不支持绑定",
                "create_tag() 会顺便生成 schema，让 font 键在设置里存在"],
         why="字体设置对应的是 Gtk::TextTag 的一个对象属性，所以代码比绑定 transition 要麻烦一些：先创建 TextTag，把设置键 font 绑定到它的 font 属性上，再把它应用到整个缓冲区。",
         ref="综合构建应用程序：用 TextTag 的属性连接字体设置"),
]

KP = dict(id="gtkmm.buildapp.quizset", title="构建应用程序测验集", difficulty=4, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-building-applications", KP, inpage, cp)
        print("written")
