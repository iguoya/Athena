import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply

MO, GT, CH, SI, SE, CX = ("sec-dropdown-model", "sec-dropdown-get", "sec-dropdown-changes",
                          "sec-dropdown-simple", "sec-dropdown-search", "sec-dropdown-complex")

INPAGE = [
    dict(id="dd12-mo-1", page=MO, pos=2,
         stem="用 Gio::ListStore<ModelColumns> 做模型，只调用了 set_model()，下拉列表能正常显示条目吗？",
         code="""
m_ListStore = Gio::ListStore<ModelColumns>::create();
// …… 往 m_ListStore 里 append 了若干 ModelColumns ……
m_DropDown.set_model(m_ListStore);""",
         right="不能：除 StringList 外，还得用 set_factory() 指定怎么显示",
         wrong=["能：DropDown 会自动显示 ModelColumns 里的 m_col_name 成员",
                "不能：set_model() 只接受 Gtk::StringList，其他模型会编译失败",
                "能：DropDown 会把每个 ModelColumns 对象的内存地址当文字显示"],
         why="DropDown 用列表模型加部件显示。模型要是 Glib::Object 的子类；只有 StringList 这种文本专用模型可以直接显示，其他模型必须用 set_factory() 设置 ListItemFactory，由工厂的信号处理函数决定每个条目显示成什么。",
         ref="DropDown 模型：除 StringList 外还需用 set_factory() 设置 ListItemFactory"),
    dict(id="dd12-mo-2", page=MO, pos=0,
         stem="DropDown 与已弃用的 ComboBox 在显示数据的方式上有什么根本不同？",
         right="DropDown 用列表模型和部件来显示；ComboBox 用树模型和单元渲染器",
         wrong=["DropDown 用树模型和单元渲染器；ComboBox 用列表模型和部件",
                "两者都用树模型，区别只是 DropDown 的下拉窗口画在窗口外面",
                "DropDown 不用模型，直接保存字符串列表；ComboBox 才需要模型"],
         why="文档写明 DropDown 是已弃用 ComboBox 的替代品：它使用列表模型而不是树模型，内容用部件而不是单元渲染器来显示。因此 DropDown 的模型定义与填充方式和 ListView、ColumnView 完全一样。",
         ref="DropDown 模型：替代已弃用的 ComboBox，用列表模型与部件而不是树模型与单元渲染器"),
    dict(id="dd12-get-1", page=GT, pos=3,
         stem="下面的代码为什么要先拿 sel 与 GTK_INVALID_LIST_POSITION 比较，再去取数据？",
         code="""
unsigned int sel = m_DropDown.get_selected();
if (sel != GTK_INVALID_LIST_POSITION)
{
  auto id = m_ListStore->get_item(sel).m_col_id;
  set_some_id_chosen(id);
}
else
  set_nothing_chosen();""",
         right="get_selected() 返回位置；没选中时是这个特殊值，不能当位置用",
         wrong=["get_selected() 返回选中项的指针，没选中时用该宏表示空指针",
                "该宏表示第 0 项，先排除它是因为第 0 项永远是占位的标题",
                "该宏用来在多线程里确认模型没有被别的线程同时修改"],
         why="get_selected() 返回无符号整数，是选中项在模型里的位置，用它再到模型里取数据；如果用户什么都没选，返回的是 GTK_INVALID_LIST_POSITION，这个值不是合法位置，必须先排除再取数据。",
         ref="DropDown 取值：get_selected() 返回位置，未选中时为 GTK_INVALID_LIST_POSITION"),
    dict(id="dd12-ch-1", page=CH, pos=1,
         stem="想在 DropDown 的选择每次变化时更新其他部件，按本章应该怎样连接信号？",
         code="""
m_DropDown.property_selected().signal_changed().connect(
  sigc::mem_fun(*this, &ExampleWindow::on_dropdown_changed));""",
         right="像这样连接 selected 属性的 signal_changed()，每次选择变化都会调用",
         wrong=["连接 DropDown 自己的 signal_changed()，ComboBox 就是这样用的",
                "连接 signal_clicked()，在每次点击下拉列表时读取最新的选择",
                "不需要连接，处理函数要靠 on_dropdown_changed() 轮询来调用"],
         why="本章写明：要对 DropDown 每一次选择变化作出反应（比如更新其他部件），连接 property_selected().signal_changed()。这与 ComboBox 的 changed 信号用法不同，迁移代码时要改。",
         ref="DropDown 选择变化：连接 property_selected().signal_changed()"),
    dict(id="dd12-sim-1", page=SI, pos=1,
         stem="用户从下拉列表选了“5 minutes”，终端会输出什么？",
         code="""
// StringList：1 minute / 2 minutes / 5 minutes / 20 minutes
m_StringList = Gtk::StringList::create(strings);
m_DropDown.set_model(m_StringList);
m_DropDown.set_selected(0);
m_DropDown.property_selected().signal_changed().connect(
  sigc::mem_fun(*this, &ExampleWindow::on_dropdown_changed));
// on_dropdown_changed 打印：
//   "DropDown changed: Row=" << selected << ", String=" << m_StringList->get_string(selected)""",
         right="只输出一行：DropDown changed: Row=2, String=5 minutes",
         wrong=["只输出一行：DropDown changed: Row=3, String=5 minutes",
                "先输出 Row=0, String=1 minute，再输出 Row=2 那一行",
                "只输出一行：DropDown changed: Row=5, String=5 minutes"],
         why="set_selected(0) 在连接信号之前调用，所以窗口显示时不会打印。用户选“5 minutes”时它在模型里的位置是 2（位置从 0 开始：1 minute 是 0，2 minutes 是 1），信号处理函数据此打印 Row=2 和对应字符串。",
         ref="DropDown 简单示例：StringList、set_selected(0) 与 on_dropdown_changed"),
    dict(id="dd12-se-1", page=SE, pos=2,
         stem="下面的示例里，为什么 Pango::FontMap 可以直接交给 DropDown 当模型？",
         code="""
// Pango::FontMap is a Gio::ListModel.
auto model = Pango::CairoFontMap::get_default();
m_DropDown.set_model(model);""",
         right="因为它实现了 Gio::ListModel 接口，凡实现该接口的类都能当模型",
         wrong=["因为 gtkmm 为 FontMap 单独写了适配器，其他类没有",
                "因为 set_model() 里专门判断了是不是 FontMap，是就走特殊路径",
                "因为 FontMap 继承自 Gio::ListStore，所以它属于一种 ListStore"],
         why="文档说明这个示例以 Pango::FontMap 为模型，之所以可行，是因为 Pango::FontMap 实现了 Gio::ListModel 接口。DropDown 只要求模型实现该接口，Gio::ListStore、Gtk::StringList、Pango::FontMap 都可以。搜索框则用 set_enable_search(true) 加 set_expression() 打开。",
         ref="DropDown 搜索示例：Pango::FontMap 实现 Gio::ListModel，所以可以直接做模型"),
    dict(id="dd12-cx-1", page=CX, pos=0,
         stem="复杂示例为什么给同一个 DropDown 设置了两个 SignalListItemFactory？",
         code="""
// Factory for presenting the selected item.
m_DropDown.set_factory(factory);
// Factory for presenting the items in the dropdown list.
m_DropDown.set_list_factory(factory);""",
         right="一个管选中项在 DropDown 上的外观，一个管展开列表里各项",
         wrong=["一个负责显示数据，另一个专门负责把用户的选择写回模型",
                "一个用于第一次显示，另一个在模型发生变化后用来替换前一个",
                "因为一个 DropDown 最多只能显示一列，第二个工厂用来显示第二列"],
         why="文档说明：如果希望下拉菜单里的条目与 DropDown 本身显示的那一项外观不同，就要再用 set_list_factory() 设置另一个 ListItemFactory。示例里列表项还带一个勾选标记，所以两套外观不同，要两个工厂各自处理 setup 与 bind。",
         ref="DropDown 复杂示例：set_factory() 管选中项，set_list_factory() 管下拉列表项"),
]

CHECKPOINT = [
    dict(id="dd12-cp-1", pos=3, locator="官方节页 sec-dropdown-model、sec-dropdown-get、sec-dropdown-changes",
         stem="把一段 ComboBox 代码迁到 DropDown，下面哪种对应关系最符合本章？",
         right="模型换成 Gio::ListModel，用 get_selected() 取位置，用 selected 属性的信号监听变化",
         wrong=["模型仍用 TreeModel，用 get_active() 取行，用 signal_changed() 监听变化",
                "模型换成 Gio::ListModel，用 get_active() 取行，用 signal_clicked() 监听变化",
                "模型仍用 TreeModel，用 get_selected() 取位置，用 property_active() 监听变化"],
         why="DropDown 用列表模型而不是树模型；选中项用 get_selected() 得到位置（没选中是 GTK_INVALID_LIST_POSITION）；选择变化连接 property_selected().signal_changed()。ComboBox 的 TreeModel、get_active()、changed 信号都不再适用。",
         ref="综合 DropDown 的模型、取值与变化信号三节"),
    dict(id="dd12-cp-2", pos=1, locator="官方节页 sec-dropdown-simple",
         stem="执行完下面的代码，s 是什么？",
         code="""
const std::vector<Glib::ustring> strings{"alpha", "beta", "gamma"};
m_StringList = Gtk::StringList::create(strings);
m_DropDown.set_model(m_StringList);
m_DropDown.set_selected(2);
auto s = m_StringList->get_string(m_DropDown.get_selected());""",
         right="“gamma”，位置从 0 开始，2 是第三项",
         wrong=["“beta”，位置 2 要减去默认已选中的第 0 项",
                "“alpha”，set_selected() 的参数被忽略，总是取第一项",
                "空字符串，因为用户还没有真正选择过任何一项"],
         why="StringList 的位置从 0 开始：alpha 是 0，beta 是 1，gamma 是 2。set_selected(2) 把选中项设成位置 2，get_selected() 就返回 2，get_string(2) 得到“gamma”。",
         ref="综合 DropDown 简单示例：StringList 的位置、set_selected() 与 get_selected()"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply("chapter-dropdown", 0, inpage, cp)
        print("written")
