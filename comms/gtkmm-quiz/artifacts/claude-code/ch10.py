import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply

DM, SM, FA, VW, SO, FI, TR = ("sec-listmodel-datamodel", "sec-listmodel-selectionmodel", "sec-listmodel-factory",
                              "sec-listmodel-view", "sec-listmodel-sorting", "sec-listmodel-filtering", "sec-listmodel-trees")

INPAGE = [
    dict(id="lm-dm-1", page=DM, pos=1,
         stem="要放进 Gio::ListStore<ModelColumns> 的条目，ModelColumns 必须满足什么要求？",
         code="""
class ModelColumns : public Glib::Object
{
public:
  int m_col_id;
  Glib::ustring m_col_name;
  static Glib::RefPtr<ModelColumns> create(int col_id, const Glib::ustring& col_name);
};

Glib::RefPtr<Gio::ListStore<ModelColumns>> m_ListStore;""",
         right="必须是 Glib::Object 的子类，条目都是它的实例，用 RefPtr 管理",
         wrong=["任何普通 C++ 结构体都行，ListStore 会按值拷贝存放",
                "必须继承 Gtk::Widget，因为条目最终要显示在界面上",
                "必须继承 Gtk::TreeModel::ColumnRecord，用来描述每一列"],
         why="Gio::ListModel 的条目（item）都是 Glib::Object 子类的实例，所以示例里 ModelColumns 继承 Glib::Object，并提供 create() 返回 RefPtr。ColumnRecord 是已弃用的 TreeView 时代的做法，Widget 则是界面部件，都不是条目的要求。",
         ref="The Data Model：条目都是 Glib::Object 子类的实例，示例 ModelColumns"),
    dict(id="lm-dm-2", page=DM, pos=3,
         stem="下面的代码执行完，“Joey Jojo” 这一项的位置（position）是多少？",
         code="""
m_ListStore = Gio::ListStore<ModelColumns>::create();
m_ListStore->append(ModelColumns::create(10, "Billy Bob"));
m_ListStore->append(ModelColumns::create(11, "Billy Bob Junior"));
m_ListStore->append(ModelColumns::create(20, "Joey Jojo"));""",
         right="2，位置从 0 开始，与条目里的 id 无关",
         wrong=["20，位置就是创建条目时给的 id 值",
                "3，位置从 1 开始计数，第 3 个条目就是 3",
                "没有固定值，只有排序之后才会给每一项分配位置"],
         why="每个条目都有一个无符号整数的位置，描述它在模型里的位置，第一项是 0：Billy Bob 是 0，Junior 是 1，Joey Jojo 是 2。位置会随着前面增删条目而变化，它和条目自己的数据（如 id）没有关系。",
         ref="The Data Model：每个条目有一个位置，第一项在位置 0，增删条目会改变位置"),
    dict(id="lm-dm-3", page=DM, pos=0,
         stem="本章列表部件用的数据模型是 Gio::ListStore，它与 Gtk::ListStore 是什么关系？",
         right="完全不同的类：Gio::ListStore 实现 Gio::ListModel，Gtk::ListStore 是已弃用的旧类",
         wrong=["是同一个类，Gtk::ListStore 是 Gio::ListStore 在 GTK 里的别名",
                "Gio::ListStore 继承自 Gtk::ListStore，增加了对大数据量的支持",
                "二者都可继续使用，Gtk::ListStore 专给 TreeView，Gio::ListStore 专给 ListView"],
         why="文档特别提醒 Gio::ListStore“不要与已弃用的 Gtk::ListStore 混淆”：前者实现 Gio::ListModel，用于 ListView/GridView/ColumnView；后者是已弃用的 TreeView 时代的类。",
         ref="The Data Model：Gio::ListStore（不要与已弃用的 Gtk::ListStore 混淆）"),
    dict(id="lm-sm-1", page=SM, pos=2,
         stem="窗口刚显示时，下面这个 ListView 里哪一项是选中的？",
         code="""
auto selection_model = Gtk::SingleSelection::create(m_StringList);
selection_model->set_autoselect(false);
selection_model->set_can_unselect(true);
m_ListView.set_model(selection_model);""",
         right="没有任何一项被选中，因为 autoselect 设成了 false",
         wrong=["第一项自动被选中，SingleSelection 总会保证有一项选中",
                "最后一项被选中，因为它是最近加入模型的条目",
                "所有条目都被选中，因为没有再选择具体的某一项"],
         why="选择模型是实现 Gtk::SelectionModel 的类，SingleSelection 只允许选一项。autoselect 默认为 true，会自动选中一项；示例把它设为 false，所以刚显示时没有选中项。",
         ref="选择模型：NoSelection、SingleSelection、MultiSelection；语义基准 docs.gtk.org SingleSelection:autoselect"),
    dict(id="lm-fa-1", page=FA, pos=0,
         stem="下面两个信号处理函数分别在什么时候做什么？",
         code="""
void ExampleWindow::on_setup_label(const Glib::RefPtr<Gtk::ListItem>& list_item)
{
  list_item->set_child(*Gtk::make_managed<Gtk::Label>("", Gtk::Align::START));
}

void ExampleWindow::on_bind_name(const Glib::RefPtr<Gtk::ListItem>& list_item)
{
  auto pos = list_item->get_position();
  auto label = dynamic_cast<Gtk::Label*>(list_item->get_child());
  label->set_text(m_StringList->get_string(pos));
}""",
         right="setup 造出空 Label；bind 把该位置的数据写进 Label",
         wrong=["setup 把数据写进 Label；bind 为列表项创建 Label 并放进去",
                "两个都在每次滚动时各创建一个新 Label，旧的由 RefPtr 回收",
                "bind 只在列表第一次显示时调用一次，之后数据变化不会再调用"],
         why="SignalListItemFactory 靠信号处理函数把模型数据放进视图：setup 在需要一个新的列表项部件时创建界面（这里是空 Label），bind 在这个列表项要显示某一位置的数据时调用，往里填数据。视图会回收滚出屏幕的列表项，再重新 bind 到新的位置。",
         ref="工厂：数据通过连接到 SignalListItemFactory 的信号处理函数加入视图"),
    dict(id="lm-vw-1", page=VW, pos=3,
         stem="为什么示例把 ListView 直接放进 ScrolledWindow，而不是随便放在某个 Box 里？",
         code="""
m_ScrolledWindow.set_child(m_ListView);
m_VBox.append(m_ScrolledWindow);""",
         right="视图靠 Scrollable 接口配合它，才知道哪些项不可见并回收",
         wrong=["ScrolledWindow 负责保存列表数据，视图只负责把数据画出来",
                "放进 ScrolledWindow 之后视图才会自动按列排序，Box 里不行",
                "这是 set_model() 的前置条件，没放进去就无法编译通过"],
         why="视图（尤其是长列表）需要知道哪些项不可见，好把它们回收。视图通过实现 Scrollable 接口、并要求直接放进 ScrolledWindow 来做到这一点。这是运行时的行为要求，与排序、编译无关。",
         ref="The View：视图实现 Scrollable 接口，期望直接放进 ScrolledWindow"),
    dict(id="lm-vw-2", page=VW, pos=1,
         stem="需要显示一张有“名称”“数值”两列、列标题可点击的表格，应该选哪个视图部件？",
         right="ColumnView，它显示一维列表，可以有一列或多列",
         wrong=["ListView，它支持多列，每一列各用一个工厂来生成部件",
                "GridView，它显示二维网格，每一行就是一列数据",
                "TreeView，本章仍推荐用它显示带多列的表格数据"],
         why="ListView 只显示一维、单列的列表；GridView 显示二维网格；ColumnView 才是一维列表加一列或多列，可以给每个 ColumnViewColumn 设置表头与排序。TreeView 已弃用，不是本章推荐的做法。",
         ref="The View：ListView（一维一列）、GridView（二维网格）、ColumnView（一维多列）"),
    dict(id="lm-vw-3", page=VW, pos=2,
         stem="某个列表项的 get_position() 返回 1，on_bind_name 会往 Label 里写什么？",
         code="""
m_StringList = Gtk::StringList::create({"Billy Bob", "Joey Jojo", "Rob McRoberts"});
...
label->set_text(m_StringList->get_string(pos));""",
         right="“Joey Jojo”，位置从 0 开始，1 是第二项",
         wrong=["“Billy Bob”，get_string() 的参数从 1 开始计数",
                "“Rob McRoberts”，位置是从列表末尾倒数的",
                "什么都不写，因为位置 1 要等排序之后才有数据"],
         why="StringList 的条目位置从 0 开始：Billy Bob 是 0，Joey Jojo 是 1，Rob McRoberts 是 2。bind 时 list_item->get_position() 给出该列表项当前对应的位置，再用它去模型里取数据。",
         ref="The View：ListView 示例 on_bind_name 用 get_position() 与 get_string()"),
    dict(id="lm-so-1", page=SO, pos=1,
         stem="下面的 SortListModel 排好序后，哪一项排在最前面？",
         code="""
// ListStore 依次追加：Billy Bob、Billy Bob Junior、Sue Bob、
//                     Joey Jojo、Rob McRoberts、Xavier McRoberts
auto size_expression = Gtk::ClosureExpression<Glib::ustring::size_type>::create(
  [](const Glib::RefPtr<Glib::ObjectBase>& item) {
    const auto col = std::dynamic_pointer_cast<ModelColumns>(item);
    return col ? col->m_col_name.size() : 0; });
m_LengthSorter = Gtk::NumericSorter<Glib::ustring::size_type>::create(size_expression);
m_LengthSorter->set_sort_order(Gtk::SortType::ASCENDING);
m_SortListModel = Gtk::SortListModel::create(m_ListStore, m_LengthSorter);""",
         right="Sue Bob，名字只有 7 个字符，升序时最短的排最前",
         wrong=["Billy Bob，SortListModel 不改变 ListStore 里的原有顺序",
                "Xavier McRoberts，升序时名字最长的反而排在最前面",
                "Billy Bob Junior，以 B 开头，按字母序靠前所以最先"],
         why="SortListModel 包住原模型，按 Sorter 给出的顺序呈现，原来的 ListStore 并不改变。NumericSorter 用名字长度作为数值、ASCENDING 升序，所以最短的 “Sue Bob”（7 个字符）排在最前。",
         ref="Sorting：用 SortListModel 包住模型并设置 Sorter（如 NumericSorter）"),
    dict(id="lm-fi-1", page=FI, pos=0,
         stem="下面的设置之后，FilterListModel 里显示哪些项？",
         code="""
m_StringFilter = Gtk::StringFilter::create(expression);   // 表达式取条目的 m_col_name
m_StringFilter->set_ignore_case(false);
m_StringFilter->set_match_mode(Gtk::StringFilter::MatchMode::SUBSTRING);
m_StringFilter->set_search("bob");
m_FilterListModel = Gtk::FilterListModel::create(m_ListStore, m_StringFilter);
// ListStore 里有：Billy Bob、Billy Bob Junior、Sue Bob、Joey Jojo ……""",
         right="一项也没有，因为区分大小写，“bob” 匹配不上 “Bob”",
         wrong=["Billy Bob、Billy Bob Junior、Sue Bob，名字里都含有 bob",
                "只有 Billy Bob，SUBSTRING 模式要求从开头开始匹配",
                "全部项，搜索词太短时 StringFilter 会自动放开过滤"],
         why="FilterListModel 包住原模型，只呈现通过 Filter 的项。StringFilter 的 ignore_case 设为 false 表示区分大小写，SUBSTRING 表示名字里含有搜索串即可：搜索“bob”匹配不到含“Bob”的名字，所以结果为空。改成 set_ignore_case(true) 才会匹配。",
         ref="Filtering：用 FilterListModel 包住模型并设置 Filter（如 StringFilter）；语义基准 docs.gtk.org StringFilter"),
    dict(id="lm-tr-1", page=TR, pos=3,
         stem="想用 ListView 显示一棵可以展开、折叠的树，本章的做法是？",
         right="用 TreeListModel 展平成列表，项里放 TreeExpander 展开折叠",
         wrong=["改回已弃用的 TreeView，Gio::ListModel 自带树结构支持",
                "给每个 ModelColumns 条目加父指针，ListView 会自动缩进显示",
                "用 FilterListModel 逐层过滤子项，再用 Notebook 一层层切换"],
         why="Gio::ListModel 本身不支持树。gtkmm 的做法是：TreeListModel 把树展平成一个列表，再在每个列表项里放 TreeExpander，用户就可以展开和折叠行。",
         ref="Displaying Trees：TreeListModel 展平树，TreeExpander 提供展开折叠"),
]

CHECKPOINT = [
    dict(id="lm-cp-1", pos=2, locator="官方节页 sec-listmodel-datamodel、sec-listmodel-selectionmodel、sec-listmodel-factory",
         stem="下面几行里，哪一部分负责“把数据变成界面上的部件”？",
         code="""
auto model = Gio::ListStore<ModelColumns>::create();
auto selection = Gtk::SingleSelection::create(model);
m_ListView.set_model(selection);
m_ListView.set_factory(factory);""",
         right="factory：用 setup/bind 处理函数造部件、填数据",
         wrong=["model：ListStore 保存数据，并为每个条目生成对应的 Label",
                "selection：SingleSelection 决定每个条目在界面上画成什么样",
                "m_ListView：视图自己直接读取 ModelColumns，再画出文字"],
         why="三者分工：模型保存数据，选择模型管理选中状态，工厂把数据放进视图（用 setup 造部件、bind 填数据），视图负责显示与交互、回收不可见项。所以“数据变部件”是工厂的职责。",
         ref="综合数据模型、选择模型与工厂：模型存数据、工厂填视图、视图显示与交互"),
    dict(id="lm-cp-2", pos=1, locator="官方节页 sec-listmodel-sorting",
         stem="用户点击 ColumnView 的“名称”列标题却没有任何排序效果，最可能漏掉了什么？",
         right="没给该 ColumnViewColumn 设置 Sorter，或没把 sorter 交给 SortListModel",
         wrong=["没有把 ColumnView 放进 ScrolledWindow，所以点击事件收不到",
                "没有为 ListStore 的条目写 create()，导致排序时无法复制条目",
                "SingleSelection 的 autoselect 设成了 false，所以排序被禁用"],
         why="ColumnView 里让用户点列标题排序，需要两步：从 ColumnView 取出 ColumnViewSorter 交给 SortListModel，并给每个 ColumnViewColumn 设置 Sorter。缺了其中一步，标题点击就没有效果。",
         ref="综合 Sorting：ColumnViewSorter 与每列的 Sorter"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply("chapter-listmodel", 0, inpage, cp)
        print("written")
