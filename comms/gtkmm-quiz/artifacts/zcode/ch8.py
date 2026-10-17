import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

LB, EN, SP = "sec-labels", "sec-text-entry", "sec-spinbutton"
PB, IB, TT = "sec-progressbar", "sec-infobar", "sec-tooltips"

INPAGE = [
    dict(id="misc8-lb-1", page=LB, pos=1,
         stem="要把标签里的一部分文字显示成粗体，该用哪个调用？",
         code="""
label->set_markup("<b>bold text</b> and <s>strikethrough text</s>");""",
         right="set_markup()，传 Pango 标记字符串",
         wrong=["set_justify()：它管整段文字的对齐方式，改不了字形",
                "set_wrap()：它开启的是自动换行，与加粗没有关系",
                "set_text()：标签不会把星号、下划线之类的记号当格式指令解析"],
         why="原文写明 Label 支持简单格式（加粗、着色、放大），做法是给 set_markup() 传一段 Pango 标记语法的字符串，如 <b>bold text</b>。set_justify() 管对齐、set_wrap() 管自动换行，set_text() 收的是纯文本，不解析任何标记。",
         ref="Label：set_markup() 使用 Pango 标记语法设置简单格式"),
    dict(id="misc8-en-1", page=EN, pos=2,
         stem="输入框初始为空。用户键入字母 g 后按回车，on_changed 与 on_activate 各被调用几次？",
         code="""
entry.signal_activate().connect(on_activate);
entry.signal_changed().connect(on_changed);""",
         right="各 1 次：键入发 changed，回车发 activate",
         wrong=["只有 on_changed 1 次：回车不改变文字，所以不发信号",
                "只有 on_activate 1 次：changed 要等焦点离开输入框才发出",
                "on_changed 2 次：键入与回车各让文字变化了一次"],
         why="原文写明 changed 在部件中的文字变化时发出，activate 在用户按下回车时发出（自 gtkmm 4.8 起）。键入一个字母是一次文字变化，回车本身不改文字、只发 activate，所以各一次。以为「回车也算一次 changed」或「changed 要等焦点离开才发」都是错的。",
         ref="Entry：activate（回车）与 changed（文字变化）的发出时机"),
    dict(id="misc8-en-2", page=EN, pos=3,
         stem="要做密码输入框：用户敲的字不能在屏幕上回显。该用哪个调用？",
         right="set_visibility(false)：让输入的文本隐藏、不回显",
         wrong=["set_editable(false)：它把输入框变成只读，用户一个字也敲不进去",
                "set_text() 清空：清空只抹掉已有内容，拦不住后面的输入回显",
                "set_activates_default(false)：它只关掉回车激活默认部件的行为"],
         why="原文写明对密码、密语这类不想在屏幕上回显的信息，给 set_visibility() 传 false 即可让文本隐藏。set_editable(false) 是设成只读——两个名字形近，管的却是「能不能敲」和「敲了显不显示」两回事。",
         ref="Entry：set_visibility(false) 隐藏密码等输入文本"),
    dict(id="misc8-sp-1", page=SP, pos=0,
         stem="官方示例的「日」微调按钮构造如下。用鼠标键 1（通常是左键）触发一次递增，值加多少？",
         code="""
m_adjustment_day( Gtk::Adjustment::create(1.0, 1.0, 31.0, 1.0, 5.0, 0.0) ),
m_SpinButton_Day(m_adjustment_day),""",
         right="1.0，鼠标键 1 用 step_increment",
         wrong=["5.0：鼠标键 1 的增量由 page_increment（第 5 个参数）决定",
                "30.0：鼠标键 1 每按下一次就跨越上下限之间的整个差值",
                "0.0：page_size 没有被使用，增量参数也跟着一并失效"],
         why="原文的属性表写明 step_increment 是「按鼠标键 1 时递增/递减的值」，page_increment 对应鼠标键 2，page_size 在 SpinButton 里未使用。create() 的第 4 个参数 1.0 就是 step_increment，所以一次递增加 1.0。",
         ref="SpinButton：Adjustment 属性表，step_increment 对应鼠标键 1"),
    dict(id="misc8-sp-2", page=SP, pos=1,
         stem="要阻止用户往微调按钮里敲非数字字符，该调用哪个方法？",
         right="set_numeric(true)：让输入框拒绝非数字字符",
         wrong=["set_wrap(true)：管的是值到上下限时是否绕回",
                "set_snap_to_ticks(true)：把值对齐到 step_increment 的倍数",
                "set_digits(0)：它只是把显示与取值舍入到整数位"],
         why="原文写明给 set_numeric() 传 true 可以阻止用户在输入框里敲非数字字符。wrap（到上下限绕回）、snap_to_ticks（对齐步长的倍数）、digits（小数位数）各管各的事，都不过滤按键。",
         ref="SpinButton：set_numeric(true) 阻止非数字输入"),
    dict(id="misc8-pb-1", page=PB, pos=2,
         stem="正在接收一个事先不知道长度的文件，进度算不成百分比。ProgressBar 该怎么用？",
         right="定时调 pulse()，显示来回移动的小矩形",
         wrong=["循环调 set_fraction() 让长条从 0 涨满再清零，冒充有进度",
                "调用 set_text() 只显示一行文字，并把长条藏起来",
                "没法用：ProgressBar 必须先知道 0.0 到 1.0 的确切进度"],
         why="原文写明当进度无法表示为数值范围时（例如接收未知长度的文件）用活动模式：进度条显示一个来回移动的小矩形，按固定间隔调用 pulse() 驱动，set_pulse_step() 可调步长。「涨满再清零」是官方示例普通模式下定时器的做法，不是活动模式。",
         ref="ProgressBar：活动模式的适用场景与 pulse() 驱动"),
    dict(id="misc8-ib-1", page=IB, pos=3,
         stem="想在当前窗口顶部给用户显示一条消息，又不弹新窗口。按本章的说法，哪项是对的？",
         right="示例改用 Box 装 Label 和 Button；InfoBar 已弃用",
         wrong=["首选 InfoBar：它显示在窗口顶部、API 与 Dialog 相似，并未弃用",
                "用 Gtk::Dialog：它和 InfoBar 一样嵌在当前窗口的顶部显示",
                "用 ProgressBar 的 set_text()：在进度条旁挂上这行消息就够了"],
         why="本章开头说 InfoBar 与 Dialog 不同：它显示在当前窗口顶部而不是另开新窗口，API 与 Dialog 很相似；但示例一节写明 InfoBar 自 gtkmm 4.10 起已弃用，示例程序改用一个 Box 装 Label 和 Button。Dialog 会另开窗口，set_text() 的位置也不对。",
         ref="InfoBar：显示在当前窗口顶部而非新窗口；自 4.10 弃用，示例用 Box+Label+Button"),
    dict(id="misc8-tt-1", page=TT, pos=0,
         stem="要让用户把指针悬停在一个按钮上几秒后看到一段文字提示，最直接的做法是？",
         right="调按钮的 set_tooltip_text()，任何部件都有",
         wrong=["new 一个 Gtk::Tooltip 对象再挂到按钮上当作它的提示窗",
                "连接 signal_query_tooltip() 并在处理函数里返回那段文字",
                "调 set_has_tooltip()，由它负责填入默认的提示文字"],
         why="原文写明用 set_tooltip_text() 就能在任何 Widget 上设置一段文字提示，指针悬停几秒即弹出。Gtk::Tooltip 与 query-tooltip 信号属于更高级的用法（例如图文并显），不是最直接的路；set_has_tooltip() 只声明「这个部件有提示」，不提供内容。",
         ref="Tooltips：set_tooltip_text() 在任意部件上设置文字提示"),
]

CHECKPOINT = [
    dict(id="misc8-cp-1", pos=1, locator="官方节页 sec-text-entry",
         stem="对话框里有一个输入框和一个 Close 按钮（已设为窗口的默认部件），输入框还调用过 set_activates_default(true)。用户在输入框里按回车，会发生什么？",
         code="""
m_Entry.set_activates_default(true);
set_default_widget(m_Button_Close);""",
         right="回车激活 Close 按钮，像被点了一样，比如把对话框关掉",
         wrong=["回车只是清空输入框，好让用户继续输入下一段内容",
                "什么都不发生：还得显式连接 activate 信号并自己转发",
                "焦点移到 Close 按钮上，但还要再按一次回车才会点它"],
         why="原文写明 set_activates_default(true) 之后，在 Entry 里按回车会激活所在窗口的默认部件——默认部件通常是对话框里的一个按钮，比如关闭对话框的那个；默认部件由 Gtk::Window::set_default_widget() 指定。整个过程不需要自己连接 activate 信号。",
         ref="综合 Entry 与窗口默认部件：set_activates_default() 的行为"),
    dict(id="misc8-cp-2", pos=2, locator="官方节页 sec-text-entry",
         stem="对一个普通的 Gtk::Entry 调用 set_progress_fraction(0.3)，屏幕上会看到什么？",
         code="""
m_Entry.set_progress_fraction(0.3);""",
         right="输入的文字下方出现一条 30% 填充的进度条",
         wrong=["看不到任何东西：进度条是 Gtk::ProgressBar 独有的功能",
                "编译失败：Gtk::Entry 根本没有这个成员方法",
                "输入框的边框被高亮成 30% 长度的一段彩色描边"],
         why="原文 Entry Progress 一节写明 Entry 可以在文本区内、所输入文字的下方显示一条进度条，只要调用过 set_progress_fraction() 或 set_progress_pulse_step() 它就会显示；官方示例正是用定时器周期调用 set_progress_fraction() 让它动起来。",
         ref="综合 Entry Progress：set_progress_fraction() 显示文字下方的进度条"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
