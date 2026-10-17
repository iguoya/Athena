import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply

CR, EA, IN = "sec-creating-adjustment", "sec-adjustments-easy", "sec-adjustment-internals"

INPAGE = [
    dict(id="ad16-cr-1", page=CR, pos=0,
         stem="只给三个参数创建 Adjustment，没写出的 step_increment、page_increment、page_size 各取多少？",
         code="""
auto adj = Gtk::Adjustment::create(50, 0, 100);
// 声明：create(double value, double lower, double upper,
//              double step_increment = 1, double page_increment = 10,
//              double page_size = 0)""",
         right="分别取默认值 1、10 和 0",
         wrong=["三个都取 0，没写的参数一律按 0 处理",
                "分别取 1、1 和 1，增量取最小单位，页大小取 1",
                "分别取 0.1、1 和 10，随取值范围的大小自动推算"],
         why="函数声明里 step_increment、page_increment、page_size 带默认值：1、10 和 0。只给 value、lower、upper 时，其余三个就是这些默认值。",
         ref="Adjustment 创建：create() 的参数与默认值（step_increment = 1，page_increment = 10，page_size = 0）"),
    dict(id="ad16-ea-1", page=EA, pos=1,
         stem="下面的代码里，用户拖动 vscrollbar 的滑块时，TextView 会怎样？",
         code="""
// creates its own adjustments
Gtk::TextView textview;
// uses the newly-created adjustment for the scrollbar as well
Gtk::Scrollbar vscrollbar(textview.get_vadjustment(), Gtk::Orientation::VERTICAL);""",
         right="TextView 跟着滚动：两者共享同一个 Adjustment，不用再写代码",
         wrong=["不会动：必须连接 value_changed，再手动调用 TextView 的滚动方法",
                "不会动：两个部件各有自己的 Adjustment，只是外观上同步",
                "会动，但前提是把滚动条放进 ScrolledWindow，否则无效"],
         why="文档说明：把一个 Adjustment 在滚动条与 TextView 之间共享，操作滚动条就会自动调整 TextView。这里滚动条用的就是 TextView 自己创建的垂直 Adjustment。",
         ref="Adjustment 的简单用法：在 Scrollbar 与 TextView 之间共享 Adjustment"),
    dict(id="ad16-ea-2", page=EA, pos=2,
         stem="下面两个部件，哪个建议让它自己创建 Adjustment，而不是自己提供？为什么？",
         right="ScrolledWindow：它的 Adjustment 用像素值，通常由滚动条间接调整",
         wrong=["SpinButton：它的 Adjustment 用像素值，范围必须由系统决定",
                "SpinButton：它把值当任意数字，Adjustment 不能由程序提供",
                "ScrolledWindow：它的 Adjustment 用任意数字，必须自己计算范围"],
         why="可调部件分两类：一类把值当任意数字（Range 部件、ScaleButton、SpinButton），由用户直接用鼠标或键盘调整；另一类（Viewport、ScrolledWindow）用像素值，通常通过滚动条间接调整，文档建议让这一类部件自己创建 Adjustment。两类部件都可以自己创建或使用你提供的 Adjustment。",
         ref="Adjustment 的简单用法：两类可调部件，Viewport 与 ScrolledWindow 用像素值"),
    dict(id="ad16-in-1", page=IN, pos=3,
         stem="要在用户拖动 Scale 时旋转图片，下面这行连接是接在谁身上的？它为什么能响应拖动？",
         code="""
adj->signal_value_changed().connect(sigc::bind<MyPicture*>(
    sigc::mem_fun(*this, &cb_rotate_picture), picture));""",
         right="接在 Scale 的 Adjustment 上；拖动改 value 时发 value_changed",
         wrong=["接在 Scale 部件上；Scale 每次重绘时都发出 value_changed",
                "接在图片对象上；Adjustment 发出 changed 通知图片刷新",
                "接在窗口上；所有可调部件的变化都由窗口统一转发"],
         why="可调部件靠 Adjustment 的 value_changed 信号同步：用户拖动改变 Adjustment 的 value，它就发出该信号；你的程序同样可以连接它。处理函数里用 get_value() 读新值，再设置图片的旋转。",
         ref="Adjustment 内部：value_changed 信号，所有可调部件都连接它，程序也可以"),
    dict(id="ad16-in-2", page=IN, pos=1,
         stem="用户往 TextView 里不断添加文字，导致 Adjustment 的 upper 变大。这时 Adjustment 发出哪个信号？",
         right="changed，范围（upper 或 lower）被重新配置时发出",
         wrong=["value_changed，只要 Adjustment 的任何字段变化都会发出它",
                "page_changed，专门用来通知页大小或范围变化的信号",
                "不发出信号，Range 部件靠定时轮询发现范围变了"],
         why="value 变了发 value_changed；而部件重新配置 upper 或 lower（比如文本变多）时发出 changed。Range 部件通常连接它来调整外观，例如滚动条滑块的大小随范围变化反比缩放。除非写新的范围部件，一般不需要自己连接它。",
         ref="Adjustment 内部：changed 信号在 upper/lower 被重新配置时发出"),
]

CHECKPOINT = [
    dict(id="ad16-cp-1", pos=2, locator="官方节页 sec-adjustments-easy 与 sec-adjustment-internals",
         stem="想在用户滚动 TextView 时更新页码标签，update_label() 里怎样得到当前的滚动位置？",
         code="""
auto adj = textview.get_vadjustment();
adj->signal_value_changed().connect(
    sigc::mem_fun(*this, &ExampleWindow::update_label));""",
         right="用 adj->get_value() 读取 Adjustment 当前的值",
         wrong=["用 textview.get_value()，TextView 自己保存了滚动位置",
                "用信号参数，value_changed 会把新值作为参数传进来",
                "用 adj->get_upper()，它总是等于当前所在的位置"],
         why="value_changed 信号不带参数；处理函数里用 get_value() 读 Adjustment 的值。upper 是范围上限（滚动内容底端的坐标），不是当前位置。滚动位置保存在 Adjustment 里，而不是 TextView 上。",
         ref="综合 Adjustment：value_changed 信号与 get_value() 读值"),
    dict(id="ad16-cp-2", pos=0, locator="官方节页 sec-creating-adjustment",
         stem="对一个内容高 500 像素、可见区域约 100 像素、刚打开在最顶部的滚动视图，下面这个 Adjustment 的各参数含义是？",
         code="""
auto adj = Gtk::Adjustment::create(0, 0, 500, 1, 10, 100);""",
         right="value 是当前位置，upper 是内容底端坐标，page_size 约为可见区域",
         wrong=["value 是内容总高度，upper 是当前位置，page_size 是步长",
                "value 是可见区域大小，upper 是步长，page_size 是内容总高度",
                "value 是步长，upper 是页增量，page_size 是内容底端坐标"],
         why="value 是初始值，通常对应可调部件最上方或最左边的位置；upper 表示滚动部件子部件最下方或最右边的坐标；page_size 大致对应可见区域。step_increment 与 page_increment 是用户改变 value 时较小与较大的两个增量。",
         ref="综合 Adjustment 创建：value、lower、upper、page_size 的含义"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply("chapter-adjustment", 0, inpage, cp)
        print("written")
