import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

SB, SC = "sec-scrollbar-widgets", "sec-scale-widgets"

INPAGE = [
    dict(id="rng7-sb-1", page=SB, pos=1,
         stem="Gtk::Scrollbar、Gtk::Scale 与 Gtk::Range 三者是什么关系？",
         right="Scale 继承 Range；Scrollbar 不继承，但与 Scale 共享许多功能",
         wrong=["Scale 和 Scrollbar 都继承自 Range，两者不同的只是水平还是垂直方向",
                "Scrollbar 继承自 Scale，它在滑块部件之上又加了一层滚动语义",
                "三者互相独立，Range 只是两个部件碰巧共用的接口约定，并无继承关系"],
         why="本节开头写明：Scale 继承自 Range，Scrollbar 并不继承 Range，但与 Scale 共享许多功能——两者都由一条滑轨（trough）和一个滑块构成。常见误解是把「功能相似」当成「继承自同一个基类」。",
         ref="Scrollbar Widgets：Scale 继承 Range，Scrollbar 不继承但共享功能"),
    dict(id="rng7-sb-2", page=SB, pos=2,
         stem="窗口里有一大段文本要能滚动浏览，本章的建议是？",
         right="用 Gtk::ScrolledWindow，多数情况下比手动放滚动条容易",
         wrong=["手动放一条标准 Scrollbar 并自己连接信号，这样才能精细控制滚动",
                "把文本外面套一层 Gtk::Frame，Frame 本来就自带滚动能力",
                "标准 Scrollbar 只能配合 Gtk::Entry 这类输入部件用，文本不行"],
         why="原文说标准滚动条应当只用来滚动另一个部件（比如 Entry 或 Viewport），而且多数情况下用 ScrolledWindow 更容易。Frame 只提供边框与标题，没有滚动能力；「只能配合 Entry」也读反了原文——Entry 只是「被滚动的部件」的例子。",
         ref="Scrollbar Widgets：标准滚动条只用于滚动另一个部件，通常 ScrolledWindow 更容易"),
    dict(id="rng7-sc-1", page=SC, pos=0,
         stem="刚构造完这个滑块，用户拖动它有意义吗？",
         code="""
auto scale = Gtk::make_managed<Gtk::Scale>();""",
         right="没意义：默认构造创建的 Adjustment 全是 0.0，要另行设置",
         wrong=["有意义：默认范围是 0.0 到 100.0、步长 1.0，拿来就能用",
                "有意义：构造时会按所在窗口的当前宽度自动确定取值范围",
                "编译报错：Scale 的构造函数要求必须传入一个现成的 Adjustment"],
         why="原文写明默认构造函数创建的 Adjustment 所有值都是 0.0，这没什么用，需要设置一些 Adjustment 细节（或直接传入配好的 Adjustment）才能得到有意义的行为。",
         ref="Scale Widgets：默认构造创建的 Adjustment 全为 0.0，需另行设置"),
    dict(id="rng7-sc-2", page=SC, pos=3,
         stem="按官方示例的参数构造下面的水平滑块。用户把它拖到某个位置后，滑轨旁显示的数值默认保留几位小数？",
         code="""
auto adj = Gtk::Adjustment::create(0.0, 0.0, 101.0, 0.1, 1.0, 1.0);
auto scale = Gtk::make_managed<Gtk::Scale>(adj, Gtk::Orientation::HORIZONTAL);""",
         right="一位小数；改位数用 set_digits()",
         wrong=["整数：Adjustment 的 value 字段本来就按整数来取舍",
                "两位小数：跟随 step_increment 的小数位数走",
                "不显示：必须先调用 set_draw_value() 才会显示数值"],
         why="Scale 默认在滑轨旁显示当前值，且默认四舍五入到一位小数——Adjustment 的 value 字段也同样取一位，set_digits() 才能改。以为「默认不显示」是记反了 set_draw_value() 的默认值：默认就是显示的。",
         ref="Scale Widgets：默认显示数值并四舍五入到一位小数，set_digits() 修改"),
]

CHECKPOINT = [
    dict(id="rng7-cp-1", pos=0, locator="官方节页 sec-range-example",
         stem="官方示例的三个部件构造如下（节选自初始化列表）。用户拖动 Scrollbar 的滑块时，两个 Scale 会怎样？",
         code="""
m_adjustment( Gtk::Adjustment::create(0.0, 0.0, 101.0, 0.1, 1.0, 1.0) ),
m_VScale(m_adjustment, Gtk::Orientation::VERTICAL),
m_HScale(m_adjustment, Gtk::Orientation::HORIZONTAL),
m_Scrollbar(m_adjustment),""",
         right="随滚动条持续同步更新，三个部件共用同一个 Adjustment",
         wrong=["保持不动：三个部件各持有独立的数值，彼此互不影响",
                "只在松开鼠标那一刻统一跳到滚动条所在的最终值",
                "不会动，除非再自己连接 value_changed 信号把值手动转发过去"],
         why="示例注释专门写明「再次复用同一个 adjustment，注意这使滚动条移动时两个滑块总是持续更新」：Adjustment 的值一变，所有关联它的部件全部随之更新，不需要手动转发信号。误以为「各动各的」是没抓住 Adjustment 的共享语义。",
         ref="综合 Range Example：三个范围部件复用同一个 adjustment 而同步"),
    dict(id="rng7-cp-2", pos=3, locator="官方节页 sec-range-example",
         stem="滚动条的 Adjustment 按官方示例构造如下。把滑块一路拖到头，adjustment 的值最大能到多少？",
         code="""
m_adjustment( Gtk::Adjustment::create(0.0, 0.0, 101.0, 0.1, 1.0, 1.0) ),
m_Scrollbar(m_adjustment),""",
         right="100.0，即 upper 减 page_size",
         wrong=["101.0：滑块一路拖到头，值自然就等于 upper 本身",
                "100.9：到头之后还要再扣掉一次 step_increment 才封顶",
                "1.0：page_size 的值本身就决定了最大能够到达的值"],
         why="示例代码注释写明：page_size 只对滚动条有意义，能达到的最高值实际是 (upper − page_size) = 101 − 1 = 100。以为「拖到头就是 upper」是最常见的误解——page_size 大致对应可见区域的大小（Adjustment 一节），滚到最后一页时值到不了 upper。",
         ref="综合 Range Example：Adjustment::create 参数注释，最高值为 upper − page_size"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
