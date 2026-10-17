import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

AC, MB, PP, GR, EX = (
    "sec-actions", "sec-menubar-and-toolbar", "sec-menus-popup", "sec-gio-resource", "sec-menus-examples")

INPAGE = [
    dict(id="mn15-ac-1", page=AC, pos=1,
         stem="菜单栏的 ui 字符串里有个菜单项写着 action='example.quit'，窗口构造时执行了下面的代码。用户点击该菜单项时会发生什么？",
         code="""
m_refActionGroup = Gio::SimpleActionGroup::create();
m_refActionGroup->add_action("quit",
  sigc::mem_fun(*this, &ExampleWindow::on_action_file_quit));
insert_action_group("example", m_refActionGroup);""",
         right="on_action_file_quit() 被调用：example.quit 是 example 组里的 quit 动作",
         wrong=["编译失败：example.quit 含点号，不是合法的动作标识符",
                "菜单项显示为灰色：动作必须先用 set_accel_for_action() 注册快捷键才能点",
                "程序弹出一个查找窗口，请用户从 example 组里挑选要执行的动作"],
         why="insert_action_group(\"example\", ...) 把整组动作以 example 为前缀挂到窗口上，XML 里的 action='example.quit' 找的就是「example 组里的 quit」，激活时调用 add_action() 登记的处理函数。以为「编译失败」是把 XML 里的字符串误当 C++ 标识符；快捷键注册与动作是否存在无关。",
         ref="Actions：add_action() 指定动作名与处理函数，insert_action_group() 给动作组加前缀"),
    dict(id="mn15-ac-2", page=AC, pos=0,
         stem="菜单和工具栏各有自己的 API，本章为什么仍建议创建 Gio::SimpleAction 来一并处理？",
         right="一个动作被菜单和工具栏同时引用，激活与启用/禁用都只处理一处",
         wrong=["动作的调用比信号处理函数快，能减少菜单弹出时的事件分发开销",
                "菜单项和工具栏按钮发不出 clicked 之类的信号，动作是唯一的响应途径",
                "建了动作就不必写 ui 字符串，菜单布局能从动作列表自动生成"],
         why="原文说这样你响应的是「动作被激活」，不必分别响应菜单项和工具栏按钮；而且通过动作可以同时启用/禁用菜单项与工具栏按钮。动作不是性能优化，菜单部件本身有信号，可见布局仍要写在 ui 字符串里。",
         ref="Actions：创建可同时被菜单和工具栏引用的 Gio::SimpleAction"),
    dict(id="mn15-mb-1", page=MB, pos=3, lang="xml",
         stem="ui 字符串里的菜单项如下。translatable='yes' 加在 label 上是为什么？",
         code="""
<item>
  <attribute name='label' translatable='yes'>_Quit</attribute>
  <attribute name='action'>example.quit</attribute>
</item>""",
         right="用户在菜单里看到的正是 label，这里标成可翻译，本地化时会一并处理",
         wrong=["标记 action 名可翻译，方便各地用户用本地名字触发动作",
                "让 Builder 把 _Quit 的 Q 显示成带下划线的助记键字母",
                "声明这个菜单项的标签允许程序在运行中动态改写"],
         why="原文说这里指定的是菜单项显示给用户看的名字，因此应该加 translatable='yes' 让这些字符串可翻译。action 名是程序内部的标识，不参与翻译；助记符来自标签里的下划线写法，与 translatable 无关。",
         ref="Menubar and Toolbar：用户可见的菜单项名字在这里指定，应标记为可翻译"),
    dict(id="mn15-mb-2", page=MB, pos=2,
         stem="从 Builder 里取菜单栏与工具栏的两段代码如下。为什么一个用 get_object<Gio::Menu>()、另一个用 get_widget<Gtk::Box>()？",
         code="""
auto gmenu = m_refBuilder->get_object<Gio::Menu>("menubar");
auto pMenuBar = Gtk::make_managed<Gtk::PopoverMenuBar>(gmenu);
m_Box.append(*pMenuBar);

auto toolbar = m_refBuilder->get_widget<Gtk::Box>("toolbar");
m_Box.append(*toolbar);""",
         right="menubar 是菜单模型，经 PopoverMenuBar 才成为部件；toolbar 本身就是部件",
         wrong=["get_object() 与 get_widget() 只是新旧两代接口，互换使用效果相同",
                "<menu> 定义弹出菜单、<object> 定义常驻部件，区别只在显示时机",
                "两段其实都能用 get_widget() 取出，示例混用两种写法只是个人风格"],
         why="原文写明用 get_object() 与 get_widget() 实例化可显示的 PopoverMenuBar 和工具栏：<menu id='menubar'> 描述的是 Gio::Menu 菜单模型（不是部件），要拿它构造 PopoverMenuBar；而 <object class='GtkBox'> 描述的本身就是部件，get_widget() 直接取出就能放进容器。两种方法并不等价。",
         ref="Menubar and Toolbar：get_object() 取菜单模型、get_widget() 取工具栏部件"),
    dict(id="mn15-pp-1", page=PP, pos=0,
         stem="弹出菜单示例的准备工作如下。用户做什么才会触发 on_label_pressed()？",
         code="""
m_refGesture = Gtk::GestureClick::create();
m_refGesture->set_button(GDK_BUTTON_SECONDARY);
m_refGesture->signal_pressed().connect(
  sigc::mem_fun(*this, &ExampleWindow::on_label_pressed));
m_Label.add_controller(m_refGesture);""",
         right="在标签上按下鼠标右键（次要鼠标键）",
         wrong=["在标签上按下鼠标左键：pressed 信号对任何按键都响应",
                "在标签之外的窗口空白处点右键：手势对整个窗口生效",
                "双击标签左键：第二次按下时才触发手势"],
         why="原文说显示弹出菜单要用 Gtk::GestureClick 并连接它的 pressed 信号；示例把按钮限定为 GDK_BUTTON_SECONDARY（次要键，通常是右键），再把控制器加到 m_Label 上。所以只有「在标签上按右键」这条路径会触发；手势只属于它被加到的那个部件。",
         ref="Pop-up Menus：用 GestureClick 的 pressed 信号触发弹出菜单"),
    dict(id="mn15-gr-1", page=GR, pos=1, lang="xml",
         stem="按下面的描述编译资源包后，rain.png 与 toolbar.ui 在进程里的资源路径是？",
         code="""
<gresources>
  <gresource prefix="/toolbar">
    <file preprocess="xml-stripblanks">toolbar.ui</file>
    <file>rain.png</file>
  </gresource>
</gresources>""",
         right="/toolbar/rain.png 与 /toolbar/toolbar.ui，前缀拼上各文件名",
         wrong=["/gresources/toolbar/rain.png 与 /gresources/toolbar/toolbar.ui",
                "/rain.png 与 /toolbar.ui：prefix 只是描述文件里的分组标签，不进路径",
                "与源文件在磁盘上的路径相同，前缀只用于查找时过滤"],
         why="原文用这个例子说明：这样的描述会创建包含 /toolbar/toolbar.ui 和 /toolbar/rain.png 两个文件资源的包——资源路径就是 gresource 的 prefix 拼上每个 file 的名字，与磁盘目录无关。",
         ref="Gio::Resource：prefix=\"/toolbar\" 的示例列出包内文件 /toolbar/toolbar.ui 与 /toolbar/rain.png"),
    dict(id="mn15-gr-2", page=GR, pos=3, lang="bash",
         stem="执行下面这条命令后，resources.c 在程序里扮演什么角色？",
         code="""
glib-compile-resources --target=resources.c --generate-source toolbar.gresource.xml""",
         right="资源包数据的 C 源码形态，链接进可执行文件",
         wrong=["一个构建脚本，构建系统运行它把资源文件安装到系统目录",
                "一份资源清单，程序启动时按它到磁盘上逐个定位资源文件",
                "给调试器看的符号表，只在开发期查看资源布局，不参与链接"],
         why="原文写明构建期间各文件被合并成一个二进制资源包并链接进可执行文件，因此加载高效（数据已在内存中）且简单（不必检查 I/O 错误或在文件系统里定位文件）。--generate-source 的产物就是这个包的 C 源码形态。",
         ref="Gio::Resource：构建时合成二进制包链接进可执行文件"),
    dict(id="mn15-ex-1", page=EX, pos=2,
         stem="官方示例的开关动作处理函数如下。删掉注释下面两行后，用户反复点菜单里的 Some Toggle，会怎样？",
         code="""
void ExampleWindow::on_menu_toggle()
{
  bool active = false;
  m_refToggle->get_state(active);

  //The toggle action's state does not change automatically:
  active = !active;
  m_refToggle->change_state(active);
  // ... 然后打印 Toggle is (not) active.
}""",
         right="处理函数每次都被调用，但状态一直停在初始值，菜单项不会打勾",
         wrong=["没有区别：GTK 收到激活会自动翻转开关动作的状态",
                "动作从此不再被激活，on_menu_toggle() 一次也不会被调用",
                "状态照常翻转，只是不再打印 Toggle is active 之类的消息"],
         why="示例注释两次强调「动作的状态不会自动改变」：激活只调用处理函数，翻转状态要靠处理函数里先 get_state() 再取反、change_state() 写回。删掉这两行后处理函数照常被调用（打印也还在），但状态永远不变。",
         ref="Main Menu example：on_menu_toggle() 中 toggle 动作状态不自动改变的注释"),
]

CHECKPOINT = [
    dict(id="mn15-cp-1", pos=0, locator="官方节页 sec-actions 与 sec-menubar-and-toolbar",
         stem="工具栏按钮的定义如下（官方示例 toolbar.ui）。C++ 代码里没有给它连接任何信号，点它为什么有反应？",
         code="""
<object class='GtkButton' id='toolbutton_quit'>
  <property name='tooltip_text' translatable='yes'>Quit</property>
  <property name='action_name'>example.quit</property>
  <property name='icon_name'>application-exit</property>
</object>""",
         lang="xml",
         right="action_name 把按钮关联到动作上，点击激活动作，由动作的处理函数响应",
         wrong=["Builder 解析 XML 时自动为它生成了 signal_clicked 的连接",
                "按钮按 id 的命名约定找到 toolbutton_quit 同名的处理函数并调用",
                "没有反应才对：不连接信号的按钮点了也不做任何事"],
         why="这正是本章开头「菜单和工具栏一起处理」的做法：动作创建后，菜单项和工具栏按钮都引用它。工具栏按钮通过 action_name 属性关联 example.quit，点击时激活动作，处理函数是 add_action() 时登记的那个，不需要也不存在针对按钮本身的信号连接。",
         ref="综合 Actions 与 Menubar and Toolbar：工具栏按钮以 action_name 关联动作"),
    dict(id="mn15-cp-2", pos=1, locator="官方节页 sec-menus-examples（Main Menu example）",
         stem="菜单里 Choice A / Choice B 两个菜单项都指向 win.choice 动作，target 分别为 a、b。用户点 Choice B 时，处理函数会发生什么？",
         code="""
m_refChoice = add_action_radio_string("choice",
  sigc::mem_fun(*this, &ExampleWindow::on_menu_choices), "a");

void ExampleWindow::on_menu_choices(const Glib::ustring& parameter)
{
  //The radio action's state does not change automatically:
  m_refChoice->change_state(parameter);
  // ...
}""",
         right="parameter 为 \"b\"；状态不自动切换，处理函数自己改",
         wrong=["parameter 为 \"a\"：创建动作时给的初始值 \"a\" 每次都原样传进来",
                "parameter 为 \"b\"；change_state() 是多余的，GTK 早已把状态改好",
                "parameter 为空串：用户选了哪项要从菜单模型里另查一遍"],
         why="单选动作（add_action_radio_string）被某个菜单项激活时，处理函数收到的 parameter 就是那个菜单项 target 属性的值，这里是 \"b\"；而与开关动作一样，单选动作的状态也不会自动切换，处理函数要自己 change_state(parameter)。窗口能直接调 add_action_radio_string，是因为 Gtk::ApplicationWindow 本身继承 Gio::ActionMap，动作带 win. 前缀，不必自建动作组。",
         ref="综合 Main Menu example：on_menu_choices() 的 parameter 与 change_state()"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
