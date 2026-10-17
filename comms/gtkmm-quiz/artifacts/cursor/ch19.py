import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

ST, ME, SIG, EX = (
    "sec-dnd-sources-targets",
    "sec-dnd-methods",
    "sec-dnd-signals",
    "sec-dnd-example",
)

INPAGE = [
    dict(id="dn19-st-1", page=ST, pos=1,
         stem="放置目标何时才会接受一次拖入？关键判据是什么？",
         right="双方 ContentFormats 有兼容格式",
         wrong=["只要两侧都挂了事件控制器，格式是否兼容都无所谓",
                "只要按住 Shift，系统会忽略格式直接允许本次放置",
                "源只要发出 drag_begin，目标就必须无条件接受拖入"],
         why="原文：源与目标各自用 Gdk::ContentFormats 声明可发送/接收的格式；只有双方有兼容格式时，放置目标才会接受拖入，并据此发出后续信号。",
         ref="Drag sources and drop targets：ContentFormats 兼容才接受"),
    dict(id="dn19-me-1", page=ME, pos=0,
         stem="下面两行执行完后，m_source_widget 在拖放里扮演什么角色？",
         code="""
auto source = Gtk::DragSource::create();
m_source_widget.add_controller(source);""",
         right="成为拖放源：挂上了 DragSource 控制器",
         wrong=["成为放置目标：create() 默认就是 DropTarget",
                "什么都不是：还得先 set_content 才能挂控制器",
                "两边都是：一个控制器同时兼任源与目标"],
         why="原文：用 Gtk::DragSource / Gtk::DropTarget 事件控制器把部件标成源或目标；示例先 create() 再 add_controller()。DropTarget 是另一类控制器，不是 DragSource::create() 的别名。",
         ref="Methods：DragSource::create + add_controller"),
    dict(id="dn19-me-2", page=ME, pos=2,
         stem="读完拖放数据后才决定拒收，应当调用 DropTarget 的哪个方法？",
         right="reject()：推迟决定后可显式拒收",
         wrong=["set_actions(0)：把动作清零就会自动拒收",
                "set_gtypes({})：清空类型列表就能挡掉本次拖入",
                "get_value() 返回空 Value，系统会替你拒收"],
         why="原文：reject() 用于「先读数据再决定是否接受」这种推迟判断的场景。set_actions / set_gtypes 是配置目标能力，不是拒收当前这次操作。",
         ref="Methods：DropTarget::reject()"),
    dict(id="dn19-sig-1", page=SIG, pos=3,
         stem="DragSource 的 prepare 槽应当返回什么？",
         code="""
source->signal_prepare().connect(
  sigc::mem_fun(*this, &Win::on_prepare), false);""",
         right="ContentProvider（拖出数据）",
         wrong=["bool：true 表示允许开始拖，false 表示取消本次",
                "Gdk::DragAction：告诉系统本次只允许 COPY 动作",
                "void：prepare 只是通知，约定上不携带任何返回值"],
         why="原文：prepare 必须返回 Gdk::ContentProvider，内含即将开始的拖拽要用的数据。bool / DragAction 是 enter、motion、drop 等其它信号的返回约定。",
         ref="Signals：DragSource::prepare 返回 ContentProvider"),
    dict(id="dn19-sig-2", page=SIG, pos=1,
         stem="drag_end 带来的那个 bool 参数表示什么？",
         right="是否为 move，源侧是否应删掉原数据",
         wrong=["拖是否成功落到目标上；失败时恒为 false",
                "用户是否按住了 Ctrl；与动作类型无关",
                "目标是否调用了 reject()；与 move/copy 无关"],
         why="原文：drag_end 提供 Gdk::Drag，以及一个 bool，说明这次是否在做 move、数据是否应当删除。它不是「是否落到目标」的总成功标志。",
         ref="Signals：drag_end 的 delete-data / move 含义"),
    dict(id="dn19-ex-1", page=EX, pos=2,
         stem="官方简易示例的 prepare 槽实际放入拖出数据的关键步骤是？",
         code="""
Glib::Value<Glib::ustring> ustring_value;
ustring_value.init(ustring_value.value_type());
ustring_value.set("I'm Data!");
return Gdk::ContentProvider::create(ustring_value);""",
         right="set 后再 create(ContentProvider)",
         wrong=["set_actions(COPY) 本身就会带上这段要拖出的字符串数据",
                "DropTarget::create 的第一个 GType 就是要发送的文本内容",
                "标签上的可见文字会自动当作拖出数据，因此无需写 prepare"],
         why="示例注释写明：数据量小时也可把 ContentProvider 存在 DragSource 上，那时甚至不必写 prepare；本例在 prepare 里构造 Value 并 create。set_actions 只声明动作；DropTarget::create 的 GType 是接收侧类型。",
         ref="Example：on_label_drag_prepare_data 返回 ContentProvider"),
]

CHECKPOINT = [
    dict(id="dn19-cp-1", pos=0, locator="官方节页 sec-dnd-example",
         stem="drop 槽收到非 ustring 的 Value 时，示例会怎样？",
         code="""
bool DnDWindow::on_button_drop_drop_data(
    const Glib::ValueBase& value, double, double)
{
  if (G_VALUE_HOLDS(value.gobj(),
        Glib::Value<Glib::ustring>::value_type()))
  {
    // ... get + cout ...
    return true;
  }
  else
  {
    std::cout << "Received unexpected data type ..." << std::endl;
    return false;
  }
}""",
         right="return false",
         wrong=["仍 return true，只是跳过字符串打印步骤",
                "抛异常，由主循环捕获后直接结束整个程序",
                "自动改成 COPY 再重试放置，直到类型终于匹配"],
         why="原文：drop 必须返回 bool 表示是否接受本次放置。示例在类型不符时打印 unexpected 并 return false；相符则取出 ustring、打印 Received、return true。",
         ref="综合 Example：drop 返回 bool；类型不符则拒收"),
    dict(id="dn19-cp-2", pos=3, locator="官方节页 sec-dnd-signals 与 sec-dnd-example",
         stem="示例源与目标都只 set_actions(COPY)。用户按住 Shift 想 move，结果？",
         right="用户选不了 move：只允许你声明过的动作",
         wrong=["系统会强制改成 MOVE，并在 drag_end 要求删源数据",
                "目标会自动升级动作，因为 Shift 优先于 set_actions",
                "prepare 会失败，因为 ContentProvider 与 MOVE 不兼容"],
         why="原文：用户只能选择你在 DragSource::set_actions 与 DropTarget::set_actions 里声明过的动作；按 Shift 想要 move 也无效，若两侧都只开了 COPY。",
         ref="综合 Signals + Example：动作集合由 set_actions 限定"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
