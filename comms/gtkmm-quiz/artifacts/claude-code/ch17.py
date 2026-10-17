import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

AL, FI, CO, FO, AB, WI = ("sec-dialogs-alertdialog", "sec-dialogs-filedialog", "sec-dialogs-colordialog",
                          "sec-dialogs-fontdialog", "sec-about-dialog", "sec-dialogs-windowdialog")

INPAGE = [
    dict(id="dg17-al-1", page=AL, pos=1,
         stem="用户按下 Escape 键时，choose_finish() 返回的 response_id 是多少？",
         code="""
m_pDialog->set_buttons({"Cancel", "Retry", "OK"});
m_pDialog->set_default_button(2); // OK button or Return key
m_pDialog->set_cancel_button(0); // Cancel button or Escape key
m_pDialog->choose(*this,
  sigc::mem_fun(*this, &ExampleWindow::on_question_dialog_finish));""",
         right="0：Escape 对应 set_cancel_button(0) 指定的下标",
         wrong=["2：Escape 与 Return 一样会触发默认按钮 OK",
                "1：按键触发时总是取按钮列表中间的那个按钮",
                "-1：用键盘关闭对话框不对应任何按钮，所以得到 -1"],
         why="AlertDialog 的按钮由 set_buttons() 按顺序给出，response_id 就是按钮下标。示例里注释写明：default 按钮（OK，下标 2）对应 Return 键，cancel 按钮（Cancel，下标 0）对应 Escape 键。",
         ref="AlertDialog 示例：set_buttons()、set_default_button() 与 set_cancel_button()"),
    dict(id="dg17-al-2", page=AL, pos=3,
         stem="同一个 Gtk::Dialog 实例会被多次显示，如果没有调用 set_hide_on_close()，用户关闭它之后会怎样？",
         code="""
dialog.set_visible(true);
// 用户关闭对话框后，程序再次 dialog.set_visible(true)""",
         right="对话框在关闭时就被销毁了，实例已不能再显示",
         wrong=["照常再次显示：关闭对话框只是隐藏，不影响下次显示",
                "自动重新创建一个内容相同的对话框，再显示出来",
                "再次显示时需要先调用 present()，此外没有区别"],
         why="文档写明：同一个对话框实例要多次显示，必须同时调用 set_hide_on_close()，否则对话框在关闭时会被销毁。想知道按了哪个按钮，就连接 response 信号，并在信号处理函数里隐藏对话框。",
         ref="Dialogs：set_visible(true) 显示；多次显示须 set_hide_on_close()，否则关闭时被销毁"),
    dict(id="dg17-al-3", page=AL, pos=2,
         stem="新项目要弹出一个简单的标准消息框，本章用的是哪个类？",
         right="Gtk::AlertDialog，4.10 起取代 MessageDialog",
         wrong=["Gtk::MessageDialog，它自 4.10 起是推荐写法",
                "Gtk::Dialog 的派生类，因为 Dialog 本身不会被弃用",
                "Gtk::Assistant，它专门用来显示简单的标准消息"],
         why="Gtk::Dialog 及其派生类自 gtkmm 4.10 起已弃用，MessageDialog 也在其中；本章示例改用 4.10 起可用的新类，简单标准消息框对应 AlertDialog。弃用的类在没有定义 GTKMM_DISABLE_DEPRECATED 时仍可使用。",
         ref="Dialogs：Dialog 及派生类自 4.10 弃用；MessageDialog 弃用、AlertDialog 自 4.10 起可用"),
    dict(id="dg17-fi-1", page=FI, pos=0,
         stem="下面三个过滤器构造好并放进 filters 之后，还需要做什么，它们才对文件对话框生效？",
         code="""
auto filters = Gio::ListStore<Gtk::FileFilter>::create();
auto filter_text = Gtk::FileFilter::create();
filter_text->set_name("Text files");
filter_text->add_mime_type("text/plain");
filters->append(filter_text);
// 另外还有 filter_cpp、filter_any，同样 append 进 filters""",
         right="调用 dialog->set_filters(filters)，把整个列表交给对话框",
         wrong=["逐个对 dialog 调用 add_filter()，每次只加一个过滤器",
                "什么都不用做，FileDialog::create() 会自动找到并使用它们",
                "把 filters 作为第一个参数传给 open()，随打开一起生效"],
         why="示例先把各个 FileFilter 追加进 Gio::ListStore，再用 dialog->set_filters(filters) 一次性交给 FileDialog，最后才调用 open() 显示。过滤器只是放进列表并不会自动生效。",
         ref="FileDialog 示例：用 Gio::ListStore<Gtk::FileFilter> 加过滤器并 set_filters()"),
    dict(id="dg17-fi-2", page=FI, pos=3,
         stem="用户在文件选择对话框里点了“取消”，下面的处理函数会走哪里？",
         code="""
try
{
  auto file = dialog->open_finish(result);
  std::cout << "File selected: " << file->get_path() << std::endl;
}
catch (const Gtk::DialogError& err)
{
  // Can be thrown by dialog->open_finish(result).
  std::cout << "No file selected. " << err.what() << std::endl;
}""",
         right="open_finish() 抛出 Gtk::DialogError，走 catch 分支",
         wrong=["open_finish() 返回空指针，try 里的代码因此崩溃",
                "open_finish() 返回一个路径为空字符串的文件对象，之后照常处理",
                "不会走到这里：取消时处理函数根本不会被调用，对话框直接关闭"],
         why="FileDialog 是异步的：open() 之后在完成回调里调用 open_finish() 取结果。没有选中文件（比如用户取消）时，open_finish() 抛出 Gtk::DialogError，所以示例用 try/catch 处理“没有选择文件”的情况。",
         ref="FileDialog 示例：open_finish() 在没有选中文件时抛出 Gtk::DialogError"),
    dict(id="dg17-co-1", page=CO, pos=1,
         stem="怎样得知用户在 ColorDialogButton 里选了新颜色？",
         code="""
m_ColorDialogButton.property_rgba().signal_changed().connect(
  sigc::mem_fun(*this, &ExampleWindow::on_color_button_color_set));""",
         right="像这样连接 rgba 属性的 signal_changed()，处理函数里读取新颜色",
         wrong=["连接按钮自己的 signal_clicked()，点击时读取当前颜色",
                "连接 ColorDialog 的 signal_color_set()，它在选定后发出",
                "不需要连接任何信号，颜色会自动写进 m_Color 变量"],
         why="ColorButton 已弃用，替代它的 ColorDialogButton 把当前颜色放在 rgba 属性里，所以示例连接 property_rgba().signal_changed()，在处理函数里取新颜色。点击按钮只是打开选择对话框，不代表颜色已经选好。",
         ref="ColorDialog 示例：ColorDialogButton 的 property_rgba().signal_changed()"),
    dict(id="dg17-fo-1", page=FO, pos=0,
         stem="迁移旧代码时，已弃用的 FontButton 在本章里对应哪个新类？",
         right="FontDialogButton，点击时打开 FontDialog",
         wrong=["FontChooserButton，是 FontButton 改名后的新类",
                "FontDialog 本身，它同时是按钮与对话框",
                "FontChooserWidget，嵌在窗口里直接显示字体列表"],
         why="自 gtkmm 4.10 起，FontChooserDialog 被 FontDialog 取代，FontButton 被 FontDialogButton 取代，后者被点击时打开字体选择对话框。ColorDialog 与 ColorDialogButton 也是同样的对应关系。",
         ref="FontDialog：FontChooserDialog→FontDialog，FontButton→FontDialogButton（自 4.10）"),
    dict(id="dg17-ab-1", page=AB, pos=2,
         stem="AboutDialog 显示出来时，用户还能选中主窗口标签里的文字吗？",
         code="""
m_Label.set_selectable(true);
// ……
m_Dialog.set_transient_for(*this);
m_Dialog.set_hide_on_close();""",
         right="能：这个 AboutDialog 是非模态的，不冻结其他窗口",
         wrong=["不能：对话框显示期间一律冻结整个应用，包括主窗口",
                "不能：set_transient_for() 会把父窗口设为只读",
                "能，但仅限第一次显示；再次显示就会冻结父窗口"],
         why="本章大多数对话框是模态的，显示时会冻结应用的其他部分；但也可以做非模态对话框，不冻结其他窗口。示例里的 AboutDialog 没有设成模态，所以主窗口里可选中的标签文字照样可以选。",
         ref="AboutDialog：本章多数对话框是模态的，示例展示非模态的 AboutDialog"),
    dict(id="dg17-wi-1", page=WI, pos=1,
         stem="自定义对话框 NameDialog 派生自 Gtk::Window，下面三行各起什么作用？",
         code="""
m_Dialog.set_transient_for(*this);
m_Dialog.set_modal();
m_Dialog.set_hide_on_close();""",
         right="设为主窗口的临时窗口、显示时冻结主窗口、关闭时只隐藏不销毁",
         wrong=["设为主窗口的子部件、显示时隐藏主窗口、关闭时销毁所有窗口",
                "设为主窗口的临时窗口、允许主窗口同时操作、关闭时销毁自己",
                "设为独立顶级窗口、显示时冻结主窗口、关闭时只隐藏不销毁"],
         why="没有合适的预定义对话框类时，可以从 Window 派生自己的对话框。set_transient_for() 把它挂在主窗口之上，set_modal() 让它显示时冻结主窗口，set_hide_on_close() 让关闭时只隐藏、以后还能再显示。",
         ref="自定义对话框：从 Window 派生，示例里的 set_transient_for()、set_modal()、set_hide_on_close()"),
]

CHECKPOINT = [
    dict(id="dg17-cp-1", pos=0, locator="官方节页 sec-dialogs-alertdialog 与 sec-dialogs-windowdialog",
         stem="一个自定义对话框要在显示期间冻结主窗口，并且之后还能再次显示同一个实例，需要哪两个调用？",
         right="set_modal() 和 set_hide_on_close()",
         wrong=["set_transient_for() 和 set_destroy_with_parent()",
                "set_resizable(false) 和 set_hide_on_close()",
                "set_modal() 和 set_visible(false)，而且要写在构造函数里"],
         why="set_modal() 让对话框显示时冻结应用的其他窗口；set_hide_on_close() 让关闭时只隐藏、不销毁，才能多次显示同一个实例。set_transient_for() 只决定它跟随哪个主窗口，不决定冻结与否。",
         ref="综合对话框：模态、关闭时隐藏、重复显示同一个实例"),
    dict(id="dg17-cp-2", pos=2, locator="官方节页 sec-dialogs-alertdialog",
         stem="用户按下 Return 键时，on_finish 里得到的 response_id 是多少？",
         code="""
m_pDialog->set_buttons({"No", "Yes"});
m_pDialog->set_default_button(1);
m_pDialog->set_cancel_button(0);""",
         right="1，对应 “Yes”：默认按钮由 Return 键触发",
         wrong=["0，对应 “No”：Return 总是取第一个按钮来触发",
                "-1，因为键盘触发不会产生有效的按钮下标，要另外处理",
                "2，下标要从按钮的个数继续往后数起来"],
         why="response_id 是 set_buttons() 里按钮的下标。set_default_button(1) 指定 “Yes” 为默认按钮，Return 键触发它；set_cancel_button(0) 指定 “No” 为取消按钮，Escape 键触发它。",
         ref="综合 AlertDialog：按钮下标、默认按钮与取消按钮"),
]

KP = dict(id="gtkmm.dialogs.quizset", title="对话框测验集", difficulty=3, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-dialogs", KP, inpage, cp)
        print("written")
