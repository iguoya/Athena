import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

MO, GET, CH = "sec-combobox-model", "sec-combobox-get", "sec-combobox-changes"
FULL, SIMPLE, ENTRY = "combobox-example-full", "combobox-example-simple", "sec-comboboxentry"

INPAGE = [
    dict(id="cb13-mo-1", page=MO, pos=0,
         stem="按官方示例的写法，模型建好、行也填完，set_model() 也调了，可下拉列表展开还是空的。最可能漏了哪一步？",
         code="""
m_refTreeModel = Gtk::ListStore::create(m_Columns);
m_Combo.set_model(m_refTreeModel);
// 已按示例填好 id、name 两列的几行数据""",
         right="还没调 pack_start()：模型里哪些列要显示，得逐列装填进视图",
         wrong=["漏了 set_active()：没有初始选中项时，列表不渲染任何行",
                "不该用 ListStore：ComboBox 只认 TreeStore，换掉才有内容",
                "set_model() 传值错了：要传 RefPtr 里的裸指针才会生效"],
         why="本章写明列表由 TreeModel 提供，而模型的列要用 pack_start()（或 pack_end()）加到组合框的视图上——官方完整示例正是在 set_model() 之后逐列 pack_start(m_col_id)、pack_start(m_col_name)。set_model() 只负责把模型交出去，不管显示哪些列。",
         ref="The model：模型的列经 pack_start()/pack_end() 加进视图"),
    dict(id="cb13-get-1", page=GET, pos=1,
         stem="界面上只显示 name 列。用户在下拉列表里选了 Joey Jojo 那行，传给 set_something_id_chosen() 的 id 是多少？",
         code="""
// 模型三行：id 列为 1、2、3，
//          name 列为 Billy Bob、Joey Jojo、Rob McRoberts
Gtk::TreeModel::iterator iter = m_Combo.get_active();
if(iter)
{
  auto row = *iter;
  auto id = row[m_Columns.m_col_id];
  set_something_id_chosen(id); // 你自己的函数
}""",
         right="2：按 id 列读值，没显示出来的列也照读",
         wrong=["Joey Jojo：选中的文本会原样传给函数",
                "1：行的编号从 1 数起，第二行就是 1",
                "编译失败：没有 pack_start 过的列不允许读取"],
         why="get_active() 返回 TreeModel::iterator，解引用成 Row 后可按任意列取值——原文举的例子正是「界面上只显示人类可读的描述，同时读模型里那一行的整数 ID」。id 是模型里存的整数，不是行号，也不是显示出来的文本。",
         ref="所选条目：get_active() 返回迭代器，解引用后可读未显示的列"),
    dict(id="cb13-ch-1", page=CH, pos=2,
         stem="用户每改选一次，你都要跟着更新窗口里的其他部件。该连接 ComboBox 的什么？",
         right="signal_changed()：每次选择变化都发出",
         wrong=["signal_clicked()：那是按钮被按下再松开时发的",
                "property_selected() 的 changed：DropDown 才这么连",
                "signal_toggled()：那是复选、开关类部件的状态信号"],
         why="本章写明：要对组合框的每次选择变化作出响应（例如更新其他部件），就处理 changed 信号，m_combo.signal_changed().connect(...)。selected 属性的信号是替代 ComboBox 的 Gtk::DropDown 那套接口；clicked、toggled 分别属于按钮类与复选/开关类部件。",
         ref="响应选择变化：处理 changed 信号"),
    dict(id="cb13-full-1", page=FULL, pos=3,
         stem="完整示例给第三列配了自定义渲染函数。模型第三行（Rob McRoberts）的 extra 列是空字符串，用户选中这一行时，第三列显示什么、什么颜色？",
         code="""
void ExampleWindow::on_cell_data_extra(
    const Gtk::TreeModel::const_iterator& iter)
{
  auto row = *iter;
  const Glib::ustring extra = row[m_Columns.m_col_extra];

  if(extra.empty())
    m_cell.property_text() = "(none)";
  else
    m_cell.property_text() = "-" + extra + "-";

  m_cell.property_foreground() =
      (extra == "yadda" ? "red" : "green");
}""",
         right="显示 (none)，颜色为绿色",
         wrong=["显示 --，颜色为绿色",
                "显示 (none)，颜色为红色",
                "第三列留空，空字符串的单元格不渲染"],
         why="extra 为空走 if 分支，文本设为 (none)；前景色只有 extra 恰好等于 yadda 时才是红色，空串不是，所以是绿色。这正是 set_cell_data_func() 的用处：每个单元格显示前都会调这个函数，文本与颜色完全由你的逻辑决定。",
         ref="Full Example：on_cell_data_extra() 按 extra 的值决定文本与前景色"),
    dict(id="cb13-simple-1", page=SIMPLE, pos=1,
         stem="按简单文本示例构造完这个 ComboBoxText，窗口刚显示时选中的是哪一项？",
         code="""
m_Combo.append("something");
m_Combo.append("something else");
m_Combo.append("something or other");
m_Combo.set_active(1);""",
         right="第二项 something else：编号从 0 数起",
         wrong=["第一项 something：没有设初始选中时默认选第一项",
                "第三项 something or other：编号从 1 数起",
                "哪项都不选：set_active() 不带项名时全都取消选中"],
         why="set_active(1) 把选中项设为编号 1 的行，编号从 0 开始，所以是第二项 something else；示例的处理函数里 get_active_text() 此时会返回它。以为「默认总选第一项」或「编号从 1 数起」都会答错。",
         ref="Simple Text Example：append() 三项后 set_active(1) 选中第二项"),
    dict(id="cb13-entry-1", page=ENTRY, pos=3,
         stem="带输入框的组合框，用户正在里面敲自定义文字。关于「怎么知道他输入完了」，本章的说法是？",
         right="changed 逐字符发出、回车不发；输入完成看 activate 与焦点离开",
         wrong=["changed 在用户按下回车时发出，正好当作输入完成的通知",
                "changed 在输入框失去焦点时才发出，失焦即完成",
                "回车会同时发出 changed 和 activate，连 changed 一个就够"],
         why="原文写明 changed（ComboBox 和 Entry 的都是）对每次文字变化发出、用户按回车时不发；按回车或把焦点移到别的部件往往才表示输入完毕，所以要连 Entry 的 activate 信号（gtkmm 4.8 起可用），并给 Entry 加 EventControllerFocus、连它的 leave。",
         ref="ComboBox with an Entry：changed 逐字符发出、回车不发；activate 与 EventControllerFocus 的 leave"),
    dict(id="cb13-entry-2", page=ENTRY, pos=2,
         stem="组合框带着输入框构造，列也装填好了。用户从下拉列表选中第一行（Billy Bob）时，输入框里出现什么？",
         code="""
ExampleWindow::ExampleWindow()
: m_Combo(true /* has_entry */)
{
  // 模型三行：m_col_id 为 1、2、3（文本列），
  //          m_col_name 为 Billy Bob、Joey Jojo、Rob McRoberts
  m_Combo.pack_start(m_Columns.m_col_name);
  m_Combo.set_entry_text_column(m_Columns.m_col_id);
  m_Combo.set_active(1);""",
         right="字符 1：进输入框的是 entry text column 指的那列",
         wrong=["Billy Bob：进输入框的是 pack_start 装填的那列",
                "空的：还得手动调 get_entry()->set_text() 填值",
                "1 Billy Bob：两列拼接后一起放进输入框"],
         why="set_entry_text_column() 指定「选中下拉项时把哪一列的值放进 Entry」——示例指定的是 m_col_id，所以进输入框的是 1；pack_start() 只管下拉列表里显示哪些列。示例还把这列建成 ustring，注释写明要选的数据必须是文本。",
         ref="ComboBox with an Entry：选中选项时 entry text column 那列的值放进 Entry"),
]

CHECKPOINT = [
    dict(id="cb13-cp-1", pos=0, locator="官方节页 sec-combobox-model 开头的提示",
         stem="接手新代码，要加一个下拉选择部件。关于 Gtk::ComboBox 的现状，本章开头的提示怎么说？",
         right="它自 4.10 起弃用，新代码用 Gtk::DropDown",
         wrong=["它与 DropDown 都在维护，按数据量选一个就行",
                "只有 ComboBoxText 弃用了，ComboBox 仍是首选",
                "弃用的是 DropDown，新代码该继续用 ComboBox"],
         why="本章开头以提示框写明：Gtk::ComboBox 与 Gtk::ComboBoxText 自 gtkmm 4.10 起已弃用，新代码请使用 Gtk::DropDown。本章随后讲的 TreeModel 与 pack_start() 用法，仍有助于理解这类模型-视图部件。",
         ref="The model：开头的弃用提示（4.10 起，新代码用 Gtk::DropDown）"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
