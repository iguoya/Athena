import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply

SI, MI = "sec-single-item-containers", "sec-multi-item-containers"

INPAGE = [
    dict(id="ctn-si-1", page=SI, pos=0,
         stem="这段代码体现了 Gtk::Paned 与 Frame 等其他单子部件容器的什么不同？",
         code="""
m_VPaned.set_start_child(m_MessagesList);
m_VPaned.set_end_child(m_MessageText);""",
         right="固定两个子部件，用 set_start_child() 与 set_end_child()",
         wrong=["Paned 可以连续 append() 任意多个子部件，它们依次排成两栏显示",
                "Paned 的两个子部件重叠显示，后设置的那个盖在前一个上面，需用 set_position() 切换",
                "两个方法只是 set_child() 的别名，任选其一设置唯一的子部件"],
         why="本节其余容器只有一个子部件，用 set_child()；Paned 把窗口分成两个窗格，子部件数固定为两个，所以用 set_start_child()/set_end_child() 分别设置，并可用 set_position() 调整分隔条位置。",
         ref="Paned：包含固定的两个子部件，用 set_start_child() 与 set_end_child()"),
    dict(id="ctn-si-2", page=SI, pos=1,
         stem="下面的 Frame 的标题会显示在哪里？",
         code="""
m_Frame.set_label("Gtk::Frame Widget");
m_Frame.set_label_align(Gtk::Align::END);""",
         right="在边框的右侧，Align::END 把标题对齐到右端",
         wrong=["在边框的左侧，Frame 的标题位置固定，不能用代码改变",
                "在边框正上方居中，Align::END 只影响标题的字体大小",
                "显示在窗口的标题栏里，与 Frame 的边框无关"],
         why="示例注释写明「Align the label at the right of the frame」：set_label_align() 控制标题沿边框的对齐，END 就是右端。Frame 用来把一个或一组部件框在带可选标题的边框里。",
         ref="Frame 示例：set_label() 设标题，set_label_align(Gtk::Align::END) 把标题对齐到右侧"),
    dict(id="ctn-si-3", page=SI, pos=2,
         stem="窗口足够大、内容很少时，下面的 ScrolledWindow 会显示哪些滚动条？",
         code="""
m_ScrolledWindow.set_policy(Gtk::PolicyType::AUTOMATIC,
                            Gtk::PolicyType::ALWAYS);""",
         right="水平滚动条不显示，垂直滚动条始终显示",
         wrong=["两个滚动条都不显示，因为内容没有超出可见区域",
                "两个滚动条都始终显示，ALWAYS 会应用到两个方向",
                "水平滚动条始终显示，垂直滚动条按需显示"],
         why="set_policy() 的两个参数依次是水平、垂直滚动条的策略。AUTOMATIC 只在内容比可见区域大时才显示滚动条，ALWAYS 则始终显示，所以这里水平方向内容放得下就不显示，垂直方向始终显示。",
         ref="ScrolledWindow：滚动条策略 AUTOMATIC 与 ALWAYS，用 set_policy() 设置；语义基准 docs.gtk.org ScrolledWindow.set_policy"),
    dict(id="ctn-si-4", page=SI, pos=3,
         stem="子部件请求 200×200，下面的 AspectFrame 实际会给它多大的空间？",
         code="""
m_AspectFrame(Gtk::Align::CENTER, Gtk::Align::CENTER,
              2.0 /* xsize/ysize = 2 */, false /* ignore child's aspect */)
m_DrawingArea.set_content_width(200);
m_DrawingArea.set_content_height(200);""",
         right="200×100：强制 2:1 宽高比，不理会子部件自己的比例",
         wrong=["200×200：子部件请求多大就给多大，比例参数只是个提示",
                "100×200：宽高比 2.0 表示高是宽的两倍，所以宽度被压缩了",
                "400×200：AspectFrame 在需要时把空间放大，补足宽度"],
         why="示例注释写明：请求 200×200 的窗口，但 AspectFrame 因为强制 2×1 的宽高比，给出的是 200×100。比例 2.0 是宽/高；最后一个参数 false 表示不采用子部件自己的比例。",
         ref="AspectFrame 示例：强制 2:1 宽高比，子部件请求 200×200 实际得到 200×100"),
    dict(id="ctn-mi-1", page=MI, pos=1,
         stem="水平 Box 里，在不考虑额外拉伸的前提下，a 与 b 之间的间距是多少像素？",
         code="""
Gtk::Box box(Gtk::Orientation::HORIZONTAL, 10);
box.append(a);
box.append(b);
b.set_margin_start(5);""",
         right="15 像素：spacing 10 加上 b 的左 margin 5",
         wrong=["10 像素：margin 只影响部件自身大小，不影响相邻部件的间距",
                "5 像素：设置了 margin 之后会覆盖 Box 的 spacing",
                "25 像素：spacing 要对 a 和 b 两边各加一次，再加 margin"],
         why="文档区分两者：spacing 是添加在相邻部件之间的（构造 Box 时指定），margin 是添加在某个部件一侧的（每个子部件单独设置）。两者叠加，所以 a 与 b 之间是 10 + 5 = 15 像素。",
         ref="Boxes（Per-container packing options）：spacing 加在部件之间，margin 加在部件一侧"),
    dict(id="ctn-mi-2", page=MI, pos=0,
         stem="m_box1 是水平方向的 Box，窗口被拉宽后，两个按钮的宽度如何变化？",
         code="""
m_box1.append(m_button1);
m_button1.set_expand();
m_box1.append(m_button2);
m_button2.set_expand();""",
         right="两个按钮一起变宽，均分多出的空间，因为都设了 expand",
         wrong=["两个按钮宽度不变，多出的空间留作窗口边缘的空白区域",
                "只有最后加入的 m_button2 变宽，前一个保持原来的宽度不变",
                "只有第一个按钮变宽，expand 对后面追加的部件不起作用"],
         why="部件默认不会在有多余空间时扩展；调用 set_expand() 后才扩展。两个子部件都扩展时，Box 把多出的空间分给它们。若都不设置，容器也不会拉伸，窗口就会出现空白。",
         ref="An improved Hello World：部件默认不扩展，set_expand() 让它扩展"),
    dict(id="ctn-mi-3", page=MI, pos=3,
         stem="下面三个按钮在网格里的位置是怎样的？",
         code="""
m_grid.attach(m_button_1, 0, 0);
m_grid.attach(m_button_2, 1, 0);
m_grid.attach_next_to(m_button_quit, m_button_1,
                      Gtk::PositionType::BOTTOM, 2, 1);""",
         right="button 1、2 在上排；Quit 在 button 1 正下方，横跨两列",
         wrong=["三个按钮排成一行：button 1、button 2、Quit 依次向右",
                "Quit 在 button 2 正下方，只占一列，左边的格子留空",
                "Quit 在 button 1 正下方，只占一列，右边的格子留空"],
         why="attach(child, 列, 行) 把按钮放到指定格子；attach_next_to() 把 Quit 放到 button 1 的 BOTTOM（下方），最后的 2, 1 是跨 2 列、占 1 行，所以 Quit 在新的一行里横跨两列。",
         ref="Grid 示例：attach() 与 attach_next_to()，两个按钮在上排，Quit 在下排跨两列"),
    dict(id="ctn-mi-4", page=MI, pos=2,
         stem="窗口出现后，用户先点“Second”页签，再点“First”页签，终端依次输出什么？",
         code="""
m_Notebook.append_page(m_Label1, "First");
m_Notebook.append_page(m_Label2, "Second");
m_Notebook.signal_switch_page().connect(sigc::mem_fun(*this,
            &ExampleWindow::on_notebook_switch_page));
// on_notebook_switch_page 打印：
//   "Switched to tab with index " << page_num""",
         right="先输出 index 1，再输出 index 0，页号从 0 开始",
         wrong=["先输出 index 2，再输出 index 1，页号从 1 开始计数",
                "只输出一次，switch_page 只在第一次切换页签时发出",
                "没有输出，必须先调用 get_current_page() 才会触发信号"],
         why="append_page() 按添加顺序给页编号，从 0 开始：First 是 0，Second 是 1。信号在连接之后每次切换页签时发出，所以点 Second 打印 index 1，再点 First 打印 index 0。",
         ref="Notebook 示例：append_page() 加页，signal_switch_page 的处理函数打印新页号"),
    dict(id="ctn-mi-5", page=MI, pos=1,
         stem="要在新项目里写一个多步骤的“向导”界面，本章对 Gtk::Assistant 怎么说？",
         right="已在 gtkmm 4.10 弃用，无 gtkmm 替代，可看 libadwaita 或 Notebook",
         wrong=["它仍是推荐做法，4.10 新增了 set_page_type() 让页面导航更方便",
                "它已改名为 Gtk::Wizard，旧名字保留用于兼容，用法完全不变",
                "它被 Gtk::Paned 取代，两个窗格分别放上一步和下一步内容"],
         why="本章写明 Gtk::Assistant 自 gtkmm 4.10 起已弃用，gtkmm 没有替代品；libadwaita（一个 C 库）有可替代的部件，某些情况下 Notebook 也可以接受。set_page_type() 是 Assistant 早就有的方法。",
         ref="Assistant：自 gtkmm 4.10 起弃用，无 gtkmm 替代，libadwaita 或 Notebook 可选"),
    dict(id="ctn-mi-6", page=MI, pos=0,
         stem="要让 Gtk::Application 把全部命令行选项交给你的信号处理函数处理，除了把选项传给 run()，还需要做什么？",
         right="给 create() 加 HANDLES_COMMAND_LINE 标志，并连接 command_line 信号",
         wrong=["在调用 run() 时把 argc 设为 1，让 Application 看不到命令行选项",
                "什么都不用做，Application 会自动把选项交给 on_activate() 处理",
                "在 main() 里自己写 getopt 循环，处理完选项之后再调用 run()"],
         why="文档给了两种方式：在 main() 里处理选项并把 argc 设为 1 来向 Application 隐藏它们；或者把全部选项交给 run()，给 create() 加 Gio::Application::Flags::HANDLES_COMMAND_LINE 标志，再连接 command_line 信号并在处理函数里解析。题问的是后一种。",
         ref="Gtk::Application and command-line options：HANDLES_COMMAND_LINE 与 command_line 信号"),
]

CHECKPOINT = [
    dict(id="ctn-cp-1", pos=3, locator="官方节页 sec-multi-item-containers",
         stem="窗口被拉高时，下面布局里哪一部分会变高？",
         code="""
m_Notebook.set_expand();
m_VBox.append(m_Notebook);
m_VBox.append(m_ButtonBox);   // 里面是一个 Quit 按钮
// m_VBox 是垂直方向的 Box""",
         right="Notebook 吃掉多出的高度，Quit 行保持原高度",
         wrong=["两部分平分多出来的高度，因为它们处在同一个 Box 里面",
                "只有 Quit 按钮所在的行变高，后追加的部件优先得到扩展",
                "哪一部分都不变，窗口拉高只会在四周增加一圈空白"],
         why="部件默认不扩展，只有设置了 set_expand() 的 Notebook 会吃掉多出来的空间；ButtonBox 没有设置扩展，保持原高度。这就是用 set_expand() 决定哪些部件吸收额外空间的做法。",
         ref="综合 Boxes：set_expand() 与部件默认不扩展的行为"),
    dict(id="ctn-cp-2", pos=2, locator="官方节页 sec-multi-item-containers",
         stem="想在 Gtk::Window 里放两个按钮，应该怎么做？",
         right="分别对窗口调用两次 set_child()，两个按钮都会显示",
         wrong=["分别对窗口调用两次 set_child()，两个按钮都会显示",
                "对窗口调用两次 append()，窗口会把它们依次排开",
                "用 Gtk::Paned，再调用三次 set_start_child() 加入三个部件"],
         why="", ref=""),
]
CHECKPOINT[1].update(
    right="先把 Box 或 Grid 这类多子部件容器设为窗口的唯一子部件，再把按钮放进去",
    wrong=["对窗口连续调用两次 set_child()，两个按钮都会显示出来",
           "对窗口调用两次 append()，窗口会把它们依次排开显示",
           "改用 Gtk::Paned，并调用三次 set_start_child() 加入三个部件"],
    why="Window 最多只能包含一个部件，所以要放多个部件就要在窗口里放一个多子部件容器，最常用的是 Gtk::Box 和 Gtk::Grid。Paned 的子部件数固定为两个，append() 是多子部件容器的方法。",
    ref="综合 Packing：窗口只能有一个子部件，用多子部件容器承载更多部件",
)

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply("chapter-container-widgets", 0, inpage, cp)
        print("written")
