import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

OV, PR, MO = "sec-keyboardevents-overview", "sec-keyboardevents-propagation", "sec-keyboardevents-mouse"

KEYFN = """
bool MyClass::on_key_pressed(guint keyval, guint, Gdk::ModifierType state)
{
  if (keyval == GDK_KEY_1 &&
    (state & (Gdk::ModifierType::SHIFT_MASK | Gdk::ModifierType::CONTROL_MASK |
     Gdk::ModifierType::ALT_MASK)) == Gdk::ModifierType::ALT_MASK)
  {
    handle_alt_press();
    return true;
  }
  return false;
}"""

INPAGE = [
    dict(id="ke23-ov-1", page=OV, pos=1,
         stem="用户只按下 Alt+1（没有同时按 Shift 或 Ctrl），下面的处理函数会怎样？",
         code=KEYFN,
         right="调用 handle_alt_press() 并返回 true，事件不再继续传播",
         wrong=["调用 handle_alt_press() 并返回 false，事件继续传播",
                "不调用 handle_alt_press()，因为 keyval 要比较的是 keycode",
                "调用 handle_alt_press()，返回值被忽略，事件照常传播"],
         why="三个修饰键掩码里只有 ALT 被按下，条件成立，处理函数调用 handle_alt_press() 并返回 true，表示信号已被完全处理，事件不再传播。返回 false 才是允许事件继续传播。",
         ref="键盘事件：key_pressed 处理函数的参数与返回值（true 表示已处理，false 允许传播）"),
    dict(id="ke23-ov-2", page=OV, pos=3,
         stem="用户按下 Ctrl+Alt+1 时，同一个处理函数会怎样？",
         code=KEYFN,
         right="不调用，返回 false：条件要求修饰键里只有 Alt",
         wrong=["调用 handle_alt_press()：只要 Alt 在其中，条件就成立",
                "调用 handle_alt_press()，因为 Ctrl 是被忽略的修饰键",
                "不调用，并返回 true，因为 Ctrl+Alt 是系统保留的组合"],
         why="条件把 state 与 SHIFT、CONTROL、ALT 三个掩码的“或”相与，再要求结果恰好等于 ALT_MASK，即三个修饰键里只有 Alt 被按下。Ctrl+Alt+1 不满足，函数最后返回 false，让事件继续传播。",
         ref="键盘事件：state 里的修饰键位标志（shift、ctrl 等）及示例中的 Alt 判断写法"),
    dict(id="ke23-ov-3", page=OV, pos=0,
         stem="连接 signal_key_pressed() 时最后的参数 false 是什么意思？",
         code="""
auto controller = Gtk::EventControllerKey::create();
controller->signal_key_pressed().connect(
  sigc::mem_fun(*this, &MyClass::on_key_pressed), false);
add_controller(controller);""",
         right="在默认处理函数之前运行（after = false）",
         wrong=["表示这个处理函数只触发一次，之后自动断开",
                "表示事件不会继续传播，相当于处理函数一定返回 true",
                "表示忽略修饰键，只比较 keyval，不读取 state 参数"],
         why="信号连接的最后一个参数 after 决定处理函数在默认信号处理函数之前（false）还是之后（true）运行。传播示例里的注释写明：const bool after = false; // Run before or after the default signal handlers.",
         ref="事件传播示例：after 参数决定在默认信号处理函数之前还是之后运行"),
    dict(id="ke23-pr-1", page=PR, pos=2,
         stem="用户在拥有键盘焦点的 Label 里按下一个键，所有处理函数都返回 false，9 个控制器里一共有几个会被调用？",
         code="""
// Window、Box、Label 三个部件上，各有三个 EventControllerKey：
controller->set_propagation_phase(Gtk::PropagationPhase::CAPTURE);
controller->set_propagation_phase(Gtk::PropagationPhase::TARGET);
controller->set_propagation_phase(Gtk::PropagationPhase::BUBBLE);""",
         right="7 个：捕获 3 个、目标只有 Label 的 1 个、冒泡 3 个",
         wrong=["9 个：每个控制器在自己的阶段都会被调用一次",
                "3 个：只有拥有键盘焦点的 Label 上的 3 个会被调用",
                "6 个：只有捕获与冒泡阶段会运行，目标阶段什么也不做"],
         why="事件分三个阶段传播：捕获阶段从顶级窗口一路向下到事件部件（Window→Box→Label），目标阶段只在事件部件上运行，冒泡阶段从事件部件向上到顶级窗口。所以 Window 和 Box 的目标阶段控制器不会被调用，总共 3 + 1 + 3 = 7 个。",
         ref="事件传播：捕获、目标、冒泡三个阶段，及 9 个 EventControllerKey 的示例"),
    dict(id="ke23-pr-2", page=PR, pos=0,
         stem="Box 的捕获阶段处理函数返回 true 之后，Label 上的处理函数还会被调用吗？",
         code="""
bool ExampleWindow::box_key_pressed(guint keyval, guint keycode,
  Gdk::ModifierType state, const Glib::ustring& phase)
{
  // 这个控制器设为 CAPTURE 阶段
  return true;
}""",
         right="不会：事件在此被取消，之后任何函数都不会再被调用",
         wrong=["会：捕获阶段的返回值只影响同一阶段的后续控制器",
                "会：事件会继续向下到 Label，只是不再向上冒泡",
                "不会，但 Label 上的目标阶段控制器仍然会被调用"],
         why="文档提醒：事件被取消（返回 true）之后，不会再有任何其他函数被调用，即使它们属于同一个部件。所以 Box 在捕获阶段返回 true，事件就到此为止，Label 的目标阶段与所有冒泡阶段处理函数都不会运行。",
         ref="事件传播：返回 true 取消事件后，不再调用任何其他函数（即使来自同一个部件）"),
    dict(id="ke23-pr-3", page=PR, pos=3,
         stem="焦点在窗口深处的某个部件时，Alt+键的助记符为什么仍然能选中菜单项？",
         right="键盘事件先发给顶级窗口，在那里检查快捷键，没处理才往下传到焦点部件",
         wrong=["助记符由焦点部件自己处理，菜单项只是把事件转发给窗口",
                "键盘事件先发给焦点部件，它忽略后再冒泡到窗口检查快捷键",
                "助记符不走事件传播，GTK 在内部直接调用菜单项的处理函数"],
         why="键盘事件首先被发送到顶级窗口，检查是否设置了键盘快捷键（加速键和助记符，用于从键盘选择菜单项）。没有被处理时，事件才向下传播到拥有键盘焦点的部件，然后再向上传播。",
         ref="事件传播：键盘事件先到顶级窗口检查加速键和助记符，再向下传播到焦点部件"),
    dict(id="ke23-mo-1", page=MO, pos=1,
         stem="下面这个 GestureClick 会响应哪些鼠标按键？",
         code="""
m_window_click = Gtk::GestureClick::create();
m_window_click->set_button(0); // All mouse buttons
m_window_click->signal_pressed().connect(
  sigc::mem_fun(*this, &ExampleWindow::on_window_mouse_pressed));
add_controller(m_window_click);""",
         right="所有鼠标按键，set_button(0) 表示不限定某个键",
         wrong=["任何按键都不响应，0 表示这个控制器被禁用",
                "只响应主按键（左键），0 是主按键的编号",
                "只响应触摸屏上的点按，鼠标按键不会触发它"],
         why="示例注释写明 set_button(0) 对应“All mouse buttons”；要限定某个键时传 GDK_BUTTON_PRIMARY、GDK_BUTTON_SECONDARY 之类的常量。处理鼠标点击用 Gtk::GestureClick，而不是键盘用的 EventControllerKey。",
         ref="鼠标事件：用 Gtk::GestureClick 处理鼠标按键，set_button(0) 表示所有按键"),
    dict(id="ke23-mo-2", page=MO, pos=2,
         stem="下面几个处理函数里，哪一个可以靠返回值来阻止事件继续传播？",
         code="""
void on_window_mouse_pressed(int n_press, double x, double y);
void on_mouse_released(int n_press, double x, double y);
void on_mouse_motion(double x, double y);
bool on_mouse_scroll(double dx, double dy);""",
         right="只有返回 bool 的 on_mouse_scroll",
         wrong=["四个都可以，只要在函数里调用 stop_propagation()",
                "on_window_mouse_pressed，按下事件总是可以被拦截",
                "on_mouse_motion，移动事件需要拦截才不会被重复处理"],
         why="许多鼠标事件的信号处理函数不返回 bool，你无法阻止这些事件继续传播。能靠返回 true 取消传播的，是返回 bool 的处理函数，例如示例里的滚轮处理函数 on_mouse_scroll。",
         ref="鼠标事件：许多信号处理函数不返回 bool，无法阻止这些事件传播"),
    dict(id="ke23-mo-3", page=MO, pos=0,
         stem="要处理鼠标滚轮（垂直滚动）事件，示例用的是哪个事件类？",
         code="""
auto mouse_scroll = Gtk::EventControllerScroll::create();
mouse_scroll->set_flags(Gtk::EventControllerScroll::Flags::VERTICAL);""",
         right="Gtk::EventControllerScroll，用 Flags::VERTICAL 限定",
         wrong=["Gtk::GestureClick，滚轮其实也是一种按键点击",
                "Gtk::EventControllerKey，滚轮事件属于键盘事件的一种",
                "Gtk::GestureZoom，它专门处理所有的滚动与缩放操作"],
         why="处理鼠标事件的事件类有好几种：点击用 GestureClick，移动用 EventControllerMotion，滚轮用 EventControllerScroll。示例里的 set_flags(VERTICAL) 让它只处理垂直滚轮转动。",
         ref="鼠标事件：GestureClick、EventControllerMotion、EventControllerScroll 等事件类；扩展示例"),
]

CHECKPOINT = [
    dict(id="ke23-cp-1", pos=1, locator="官方节页 sec-keyboardevents-overview",
         stem="用户按下 Shift+Alt+1 时，下面哪个判断成立？",
         code="""
// 判断 A
(state & Gdk::ModifierType::ALT_MASK) == Gdk::ModifierType::ALT_MASK
// 判断 B
(state & (Gdk::ModifierType::SHIFT_MASK | Gdk::ModifierType::CONTROL_MASK |
          Gdk::ModifierType::ALT_MASK)) == Gdk::ModifierType::ALT_MASK""",
         right="A 成立，B 不成立：B 要求三个修饰键里只有 Alt",
         wrong=["A 与 B 都成立，因为 Alt 都在其中",
                "A 不成立，B 成立，因为 Shift 会抵消 Alt",
                "A 与 B 都不成立，Shift+Alt 不是合法的组合"],
         why="A 只检查 Alt 位，Shift+Alt 里包含 Alt，所以成立；B 先用 SHIFT、CONTROL、ALT 三个掩码取出这三位，再要求结果恰好是 ALT，Shift 同时按下时结果多了 SHIFT 位，所以不成立。示例用 B 的写法来区分 Alt+1 与 Shift+Alt+1。",
         ref="综合键盘事件：用位掩码判断修饰键组合"),
    dict(id="ke23-cp-2", pos=3, locator="官方节页 sec-keyboardevents-propagation",
         stem="想在事件到达拥有焦点的部件之前先拦截键盘事件，控制器应设成哪个传播阶段？",
         code="""
controller->set_propagation_phase(Gtk::PropagationPhase::____);
add_controller(controller);   // 加在顶级窗口或某个祖先部件上""",
         right="CAPTURE：捕获阶段从顶级窗口向下运行，先于焦点部件",
         wrong=["BUBBLE：冒泡阶段先从祖先部件开始，再到焦点部件",
                "TARGET：目标阶段在所有祖先部件上都会先运行一次",
                "NONE：不设置阶段时控制器总是最先收到事件"],
         why="捕获阶段从顶级窗口向下运行到事件部件，所以加在祖先部件上、设成 CAPTURE 的控制器会先于焦点部件收到事件，并且可以返回 true 来拦截。TARGET 只在事件部件上运行，BUBBLE 是从事件部件向上走。",
         ref="综合事件传播：捕获阶段先于目标阶段，从顶级窗口向下运行"),
]

KP = dict(id="gtkmm.keyboardevents.quizset", title="键盘与鼠标事件测验集", difficulty=3, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-keyboardevents", KP, inpage, cp)
        print("written")
