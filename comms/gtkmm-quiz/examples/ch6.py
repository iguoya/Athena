import json
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "tools"))
import quizlib
from quizlib import build, report, CUR

PB, TB, CB, RB = "sec-pushbuttons", "sec-toggle-buttons", "sec-checkbuttons", "sec-radio-buttons"

PUSH = [
    dict(id="btn6-pb-1", page=PB, pos=1,
         stem="按钮显示出来之后，用户按下键盘上的 Alt+H，会发生什么？",
         code="""
auto button = Gtk::make_managed<Gtk::Button>("_Help", true);""",
         right="按钮被触发，效果和鼠标点击一样，会发出 clicked 信号",
         wrong=["没有反应，助记符只能配合 Ctrl 键触发，Alt 无效",
                "只是把键盘焦点移到按钮上，还要再按一次回车才触发",
                "按钮上直接显示“_Help”，下划线只是个普通字符"],
         why="构造函数的第二个参数 true 表示标签里的下划线标出助记符：“_Help” 显示为带下划线的 Help，Alt+H 相当于点击这个按钮。去掉 true，下划线才只是普通字符。",
         ref="Button：在字符前加下划线并把 mnemonic 参数设为 true，定义键盘助记符"),
    dict(id="btn6-pb-2", page=PB, pos=2,
         stem="下面的代码运行后，这个按钮在窗口里看起来是什么样？",
         code="""
auto pmap = Gtk::make_managed<Gtk::Image>("info.xpm");
auto label = Gtk::make_managed<Gtk::Label>("cool button");
auto hbox = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 5);
hbox->append(*pmap);
hbox->append(*label);
m_button.set_child(*hbox);""",
         right="一个按钮，里面横向并排放着图片和文字“cool button”",
         wrong=["两个互不相干的部件：左边是按钮，右边是图片和文字",
                "只显示图片，set_child() 只收一个部件，标签被直接丢弃了",
                "编译失败，Gtk::Button 不是容器，没有 set_child() 方法"],
         why="Gtk::Button 本身也是容器，可以把别的部件放进去。这里把装着 Image 和 Label 的 Box 作为按钮的唯一子部件，所以点击按钮的任意位置都会触发 clicked。",
         ref="Button：Gtk::Button 也是容器，示例把 Image 与 Label 装进 Box 再放进按钮"),
    dict(id="btn6-pb-3", page=PB, pos=0,
         stem="用户在按钮上按下鼠标左键，但还没有松开。此时 clicked 信号的情况是？",
         right="还没发出，要等按下并松开之后才发出",
         wrong=["已经发出，松开鼠标时会再发出一次",
                "已经发出一次，松开鼠标时不会再发出",
                "不会发出，clicked 只在用键盘激活按钮时才发出"],
         why="文档写明 clicked 在按钮被按下并释放之后发出，不是按下的那一刻。想在按下时就做事，要用别的机制，不能指望 clicked。",
         ref="Button：clicked 信号在按钮被按下并释放时发出"),
]

TOGGLE = [
    dict(id="btn6-tb-oq1", type="observation_quiz", demo_ref="demo.buttons", page=TB, pos=3,
         stem="打开真机演示，点击「切换我」两次：最后一次发出的 toggled 信号 detail 是什么、此时 get_active() 返回多少？",
         right="detail 为 inactive，get_active() 返回 false",
         wrong=["detail 为 active，get_active() 返回 true",
                "第二次点击不再发信号，状态仍然为 true",
                "两次 detail 都是 active，get_active() 为 true"],
         why="ToggleButton 创建时是弹起（false）。第一次点击变为按下，发出 toggled（active）；第二次点击弹起，再发出 toggled（inactive），此时 get_active() 为 false。每次状态变化都会发信号。",
         ref="演示 demo.buttons：toggle 行的 toggled 信号及 get_active() 状态"),
    dict(id="btn6-tb-2", page=TB, pos=0,
         stem="用户对刚创建的 ToggleButton 依次点击 3 次，终端会输出什么？",
         code="""
toggle.signal_toggled().connect([&toggle] {
  std::cout << toggle.get_active() << ' ';
});""",
         right="1 0 1",
         wrong=["true false true",
                "1 1 1",
                "0 1 0"],
         why="ToggleButton 创建时是弹起（false），每次点击翻转一次并发出 toggled：按下（1）、弹起（0）、按下（1）。std::cout 输出 bool 默认打印 1/0 而不是 true/false，除非设置了 boolalpha。",
         ref="ToggleButton：get_active() 在按钮按下时为 true；CheckButton 与 ToggleButton 创建时都是关闭状态"),
]

CHECK = [
    dict(id="btn6-cb-1", page=CB, pos=2,
         stem="有人说“Gtk::CheckButton 是 Gtk::ToggleButton 的子类”。本章怎么说？",
         right="CheckButton 直接继承自 Gtk::Widget，并非子类；二者成员方法相同，只是外观不同",
         wrong=["说得对，CheckButton 继承自 ToggleButton，可以当 ToggleButton 用",
                "说得对，它们是同一个类，只是 Glade 里叫法不同而已",
                "不对，CheckButton 继承自 Gtk::Button，所以有 clicked 信号"],
         why="本章明确写道 Gtk::CheckButton 直接继承自 Gtk::Widget，与 ToggleButton 相似，唯一实质区别是外观；读写状态用同样的成员方法（get_active()/set_active()）。",
         ref="CheckButton：CheckButton 直接继承自 Gtk::Widget，与 ToggleButton 只有外观不同"),
    dict(id="btn6-cb-2", page=CB, pos=3,
         stem="用户勾选这个初始未选中的 CheckButton，终端会输出什么？",
         code="""
m_button.signal_toggled().connect(sigc::mem_fun(*this,
            &ExampleWindow::on_button_toggled));

void ExampleWindow::on_button_toggled()
{
  std::cout << "The Button was toggled: state="
      << (m_button.get_active() ? "true" : "false")
      << std::endl;
}""",
         right="The Button was toggled: state=true",
         wrong=["The Button was toggled: state=false",
                "没有输出，因为只连接了 toggled，没有连接 clicked",
                "输出两行，按下和松开各触发一次 on_button_toggled"],
         why="toggled 是在状态改变之后发出的，处理函数里 get_active() 读到的已经是新状态 true。toggled 每次状态变化只发一次，不是按下、松开各一次。",
         ref="CheckButton 官方示例：on_button_toggled() 用 get_active() 打印当前状态"),
]

RADIO = [
    dict(id="btn6-rb-1", page=RB, pos=1,
         stem="下面的代码执行完，窗口刚显示时，这三个按钮各是什么状态？",
         code="""
auto rb1 = Gtk::make_managed<Gtk::CheckButton>("button1");
auto rb2 = Gtk::make_managed<Gtk::CheckButton>("button2");
auto rb3 = Gtk::make_managed<Gtk::CheckButton>("button3");
rb2->set_group(*rb1);
rb3->set_group(*rb1);""",
         right="三个都没有选中，需要自己用 set_active() 打开其中一个",
         wrong=["rb1 自动选中，因为它是组里的第一个成员",
                "三个都选中，因为它们现在共享同一个状态",
                "三个按钮中随机选中一个，显示时由 GTK 决定"],
         why="CheckButton 与 ToggleButton 创建时都是关闭的，成组之后三个仍然全部是关闭。文档特别提醒：别忘了用 set_active() 打开其中一个，否则用户看到的是一组全空的单选项。",
         ref="RadioButton：成组后默认全部关闭，别忘了用 set_active() 打开一个"),
    dict(id="btn6-rb-2", page=RB, pos=0,
         stem="接上题，执行下面几行之后，rb1->get_active() 与 rb2->get_active() 分别是？",
         code="""
rb1->set_active(true);
rb2->set_active(true);   // 用户随后选了 button2""",
         right="false 和 true，同组里只能有一个被选中",
         wrong=["true 和 true，因为两次调用互相独立，互不影响",
                "true 和 false，因为先选中的按钮优先，后来的被忽略",
                "false 和 false，因为成组后需要全部取消再重新选择"],
         why="成组的按钮互斥：在同一组里选中一个，其余的自动变为关闭。后选中的 rb2 为 true，原来选中的 rb1 变为 false。",
         ref="RadioButton：同组里同一时间只有一个按钮可以被选中"),
    dict(id="btn6-rb-3", page=RB, pos=2,
         stem="只要把三个 CheckButton 放进同一个 Gtk::Box，它们就会互斥吗？",
         right="不会。互斥来自 set_group() 建立的分组，与摆放位置无关",
         wrong=["会。同一个容器里的 CheckButton 自动成为一组",
                "会。只要给它们设置相同的标签前缀，就自动成组",
                "不会。互斥只能靠连接 toggled 信号，在处理函数里手动取消"],
         why="GTK4 里没有独立的单选按钮类，CheckButton 和 ToggleButton 在被加入同一个组后才表现为单选。分组是显式的 set_group() 调用，不由容器或标签推断。",
         ref="RadioButton：没有独立的单选按钮类，成组的 CheckButton 才表现为单选"),
]

CHECKPOINT = [
    dict(id="btn6-cp-1", pos=3, locator="官方节页 sec-radio-buttons 与 sec-checkbuttons",
         stem="把下面 GTK3 时代的代码迁到 GTK4，互斥单选应该怎么改？",
         code="""
Gtk::RadioButton::Group group;
Gtk::RadioButton rb1(group, "button1");
Gtk::RadioButton rb2(group, "button2");""",
         right="改用 Gtk::CheckButton，让 rb2 用 set_group() 加入 rb1 所在的组",
         wrong=["保留 Gtk::RadioButton，只需要换成 GTK4 的头文件",
                "改用 Gtk::ToggleButton，并把它们放进同一个 Gtk::Box",
                "改用 Gtk::Switch，并给每个 Switch 都调用 set_group()"],
         why="GTK4 没有独立的 RadioButton 类：CheckButton 与 ToggleButton 通过 set_group() 加入同一组即可互斥。用 Box 摆放或换成 Switch 都不会产生互斥。",
         ref="综合 CheckButton 与 RadioButton：GTK4 用成组的 CheckButton 实现单选"),
    dict(id="btn6-cp-2", pos=1, locator="官方节页 sec-pushbuttons 与 sec-toggle-buttons",
         stem="用户依次点击 A 一次、B 两次，on_a 与 on_b 各被调用几次？",
         code="""
Gtk::Button a("A");
a.signal_clicked().connect(on_a);
Gtk::ToggleButton b("B");
b.signal_toggled().connect(on_b);""",
         right="on_a 1 次、on_b 2 次，每次状态变化都发出 toggled",
         wrong=["on_a 1 次、on_b 1 次，ToggleButton 只在第一次按下发信号",
                "on_a 1 次、on_b 4 次，每次点击按下与松开各发一次",
                "on_a 2 次、on_b 2 次，每次点击同时发出 clicked 和 toggled"],
         why="Button 每点击一次（按下并松开）发出一次 clicked；ToggleButton 每次状态变化发出一次 toggled，点击两次就是两次状态变化。两种信号分别属于两种按钮，不会同时出现。",
         ref="综合 Button 与 ToggleButton：clicked 与 toggled 的发出时机"),
    dict(id="btn6-cp-3", pos=2, locator="演示 demo.buttons",
         stem="（演示观察）在真机演示中勾选「勾选我」，status 显示与事件面板收到的信号分别是？",
         right="get_active() = true；signal toggled（detail: active）",
         wrong=["get_active() = false；signal clicked",
                "没有信号发出，状态栏保持原样",
                "signal pressed（detail: true）；get_active() 未更新"],
         why="CheckButton 与 ToggleButton 一样，状态变化后发出 toggled：勾选后 get_active() 为 true，演示事件面板收到 detail 为 active 的 toggled。",
         ref="演示 demo.buttons：check 行的 toggled 信号及 get_active() 状态"),
    dict(id="btn6-cp-4", pos=0, locator="官方节页 sec-radio-buttons",
         stem="执行完下面的代码，rb2->get_active() 与 rb3->get_active() 的值是？",
         code="""
rb2->set_group(*rb1);
rb3->set_group(*rb1);
rb1->set_active(true);""",
         right="都是 false，三个成员里只有 rb1 被选中",
         wrong=["都是 true，成组后三个按钮同步变化",
                "rb2 为 true、rb3 为 false，按加入顺序依次选中",
                "rb2 为 false、rb3 为 true，后加入组的成员会自动被选中"],
         why="三个按钮已加入同一组，组内只能有一个被选中；现在选中的是 rb1，所以 rb2 与 rb3 都是 false。成组并不意味着同步变化，而是互斥。",
         ref="综合 RadioButton：分组后同一时间只有一个按钮被选中"),
]


def build_all():
    out = {}
    for name, specs in (("push", PUSH), ("toggle", TOGGLE), ("check", CHECK + RADIO)):
        out[name] = [build(s) for s in specs]
    out["cp"] = [build(s) for s in CHECKPOINT]
    return out


def apply_kp(data_section, kp_index, new_quizzes):
    """按位置顺序把 KP 里的旧题换成新题，其余块（text/code/simulation/demo/experiment…）原位不动。"""
    blocks = data_section["knowledge_points"][kp_index]["blocks"]
    out, it = [], iter(new_quizzes)
    for b in blocks:
        if b["type"] in ("quiz", "observation_quiz"):
            nxt = next(it, None)
            if nxt is not None:
                out.append(nxt)
        else:
            out.append(b)
    out.extend(it)
    data_section["knowledge_points"][kp_index]["blocks"] = out


if __name__ == "__main__":
    b = build_all()
    allitems = b["push"] + b["toggle"] + b["check"] + b["cp"]
    report(allitems)
    if "--apply" in sys.argv:
        raw = CUR.read_bytes().decode("utf-8")
        nl = "\r\n" if "\r\n" in raw else "\n"
        data = json.loads(raw.replace("\r\n", "\n"))
        sec = next(s for s in data["sections"] if s["id"] == "chapter-button-widget")
        apply_kp(sec, 0, b["push"])
        apply_kp(sec, 1, b["toggle"])
        apply_kp(sec, 2, b["check"])
        sec["checkpoint"] = b["cp"]
        sec["quiz_standard"] = 2
        # 手写知识点正文里的错误：GTK4 的 CheckButton 直接继承自 Gtk::Widget，不是 ToggleButton
        for blk in sec["knowledge_points"][2]["blocks"]:
            if blk["type"] == "text" and "语义上继承自 Gtk::ToggleButton" in blk["text"]:
                blk["text"] = ("Gtk::CheckButton 是勾选框，视觉是圆圈或对勾。它直接继承自 Gtk::Widget（并不是 "
                               "Gtk::ToggleButton 的子类），但与 ToggleButton 用法相同：同样用 toggled 信号与 get_active()。")
        out = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        CUR.write_bytes(out.replace("\n", nl).encode("utf-8"))
        print("written")
