import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

MO, VI, IT = "sec-treeview-model", "sec-treeview", "sec-iterating-over-model-rows"
SE, SO, DD, CM, EX = ("sec-treeview-selection", "sec-treeview-sort",
                      "sec-treeview-draganddrop", "sec-treeview-contextmenu",
                      "sec-treeview-examples")

INPAGE = [
    dict(id="tv11-mo-1", page=MO, pos=2,
         stem="模型列 m_col_text 声明为 TreeModelColumn<Glib::ustring>。下面这行代码会怎样？",
         code="""
int number = row[m_Columns.m_col_text];""",
         right="编译不通过：取值走列的编译期类型检查",
         wrong=["编译通过，运行到这行时抛出类型不匹配的异常",
                "编译通过，number 得到字符串的字符个数",
                "编译通过，number 得到 0，转换不了就给默认值"],
         why="TreeModelColumn<T> 让 row[...] 的存取都带着类型：ustring 到 int 没有转换路径，编译器直接报错。原文正是用这行代码演示「使用不合适的类型会生成编译错误」——错误在编译期暴露，不会拖到运行时才炸。",
         ref="The Model：用不合适的类型取值会生成编译错误（ustring 到 int 无转换）"),
    dict(id="tv11-mo-2", page=MO, pos=0,
         stem="ListStore 与 TreeStore 各自适合放什么数据？",
         right="TreeStore 的行可以有子行；ListStore 的行没有子行",
         wrong=["ListStore 只能放数字，TreeStore 才能放文本和图标",
                "ListStore 的数据在内存里，TreeStore 的数据在磁盘文件里",
                "TreeStore 支持点击列头排序，ListStore 不支持排序"],
         why="原文：ListStore 是简单的数据行，每行都没有子行；TreeStore 的每行可能有子行，子行还能再挂子行。放什么类型由列声明决定，两种模型都一样；排序来自 TreeSortable，两种标准模型都派生自它，并非 TreeStore 独有。",
         ref="The Model：ListStore 无子行，TreeStore 每行可能有子行"),
    dict(id="tv11-vi-1", page=VI, pos=3,
         stem="m_TreeView.append_column(\"Messages\", m_Columns.m_col_text) 没有指定 CellRenderer，这列会怎样显示？",
         right="自动选合适的 CellRenderer，通常正是需要的",
         wrong=["空白：要先 set_cell_data_func() 教它怎么显示",
                "编译不通过：这个重载只接受数值类型的模型列",
                "显示列标题 Messages，单元格里没有内容"],
         why="原文：用这种简单的 append_column() 重载时，TreeView 会以合适的 CellRenderer 显示模型数据——字符串和数字用简单的部件，布尔值显示为复选按钮，这通常就是你要的；其他列类型才需要 set_cell_data_func() 转成字符串，或派生自定义 CellRenderer。",
         ref="The View：简单 append_column() 重载自动选用合适的 CellRenderer"),
    dict(id="tv11-vi-2", page=VI, pos=1,
         stem="要让「图标 + 名称」出现在同一个视图列里，官方示例怎么做？",
         code="""
auto pColumn = Gtk::make_managed<Gtk::TreeView::Column>("Icon Name");
pColumn->pack_start(m_columns.icon, /* expand= */ false);
pColumn->pack_start(m_columns.iconname);
m_TreeView.append_column(*pColumn);""",
         right="手动建列对象，用 pack_start() 装入两个模型列",
         wrong=["调两次 append_column()，让两列紧挨着显示",
                "把图标嵌进字符串列，用 Pango 标记混在文本里",
                "做不到：GTK 规定一个视图列只能绑定一个模型列"],
         why="原文：要在一个视图列里渲染多个模型列，需要手动创建 TreeView::Column 部件并用 pack_start() 把模型列装进去，再 append_column() 加到视图——示例正是把 pixbuf 图标与文字装进同一列。append_column() 有两个重载：收预建好的 Column，或收单个模型列自动生成。",
         ref="The View：TreeView::Column 与 pack_start() 在一个视图列里渲染多个模型列"),
    dict(id="tv11-it-1", page=IT, pos=0,
         stem="要遍历模型的全部顶级行，下面的写法对吗？",
         code="""
for (auto row : refModel->children())
{
  //Do something with the row.
}""",
         right="对：children() 是标准库风格的容器，可直接 range-for",
         wrong=["编译不过：children() 返回迭代器，不能用于 range-for",
                "能编译，但只遍历到第一个子行的后代行",
                "能编译，但每轮循环拿到的是列，不是行"],
         why="原文：TreeModel 通过 children() 提供 C++ 标准库风格的子行容器，可以用熟悉的 begin()/end()；要遍历整个范围时用 range-based for 更简洁，循环变量就是 Row 本身。TreeStore 想再往下一层时，对 Row 调 row.children()。",
         ref="遍历模型行：children() 容器与 range-based for 循环"),
    dict(id="tv11-se-1", page=SE, pos=2,
         stem="默认单选模式下用户点选了一行。这段代码里的 iter 是什么？",
         code="""
auto refTreeSelection = m_TreeView.get_selection();
auto iter = refTreeSelection->get_selected();
if(iter) //If anything is selected
{
  auto row = *iter;
}""",
         right="指向选中行的迭代器；没选中时为空，可用 if 判断",
         wrong=["选中行的行号：一个从 0 数起的整数",
                "全部选中行的列表，多选模式下才有多个元素",
                "选中行的路径字符串，格式如 \"3\" 或 \"3:2\""],
         why="原文：先 get_selection() 拿到 Selection 对象；默认只允许单选，直接 get_selected() 拿迭代器，用 if(iter) 判断是否选中了东西，解引用得到 Row。多选模式才需要 get_selected_rows() 或 selected_foreach 系列回调。",
         ref="选择：get_selection() 与单选模式下的 get_selected()"),
    dict(id="tv11-se-2", page=SE, pos=1,
         stem="gtk-demo 不希望用户选中分类节点。这个 select_function 起什么作用？",
         code="""
bool DemoWindow::select_function(
    const Glib::RefPtr<Gtk::TreeModel>& model,
    const Gtk::TreeModel::Path& path, bool)
{
  const auto iter = model->get_iter(path);
  return iter->children().empty();
}""",
         right="只允许叶子行被选中，有子行的行点选不上",
         wrong=["只允许分类节点被选中，叶子行反而选不上",
                "把没有子行的行全部自动选中",
                "不影响能否选中，只决定选中后的高亮颜色"],
         why="原文：set_select_function() 用来控制哪些行可以被选中；gtk-demo 里选中一个 demo 看源代码有意义，选中 demo 分类没有意义。示例返回 children().empty()——没有子行（叶子）才返回 true 允许选中。返回值管的是「允许与否」，不是选中样式。",
         ref="选择：set_select_function() 示例只允许叶子节点被选中"),
    dict(id="tv11-so-1", page=SO, pos=3,
         stem="想让用户点击 TreeView 的列标题就按那一列排序，该调用哪个？",
         right="视图列的 set_sort_column()，传入要排序的模型列",
         wrong=["模型列自己的 set_sort_column()，点列头时自动触发",
                "连接列头的 signal_clicked()，在回调里手动重排各行",
                "set_sort_func() 传比较回调，简单排序也得自己写函数"],
         why="原文：要让用户点击列头就排序，调 Gtk::TreeView::Column::set_sort_column() 并传模型列。模型自身的 set_sort_column() 是直接设当前排序列，不挂在列头上；set_sort_func() 留给更复杂的排序算法，简单排序用不着；也不需要手动重排——TreeSortable 已经提供了排序。",
         ref="排序：TreeView::Column::set_sort_column() 让列头可点击排序"),
    dict(id="tv11-so-2", page=SO, pos=0,
         stem="TreeView 显示的是 TreeModelSort。示例的删除按钮为什么要先转换迭代器？",
         code="""
auto sorted_iter = m_refTreeSelection->get_selected();
if(sorted_iter)
{
  auto iter = m_refModelSort->convert_iter_to_child_iter(sorted_iter);
  m_refModel->erase(iter);
}""",
         right="选中给的迭代器属于排序模型，底层模型不认它",
         wrong=["排序模型是只读的，转换成子模型迭代器才能写",
                "不转换也能 erase，转换只是省一次查找",
                "转换成路径再删，因为 erase 只接受路径参数"],
         why="原文：TreeView 提供的迭代器指向排序模型，必须转换成底层子模型的迭代器，才能在那个模型上执行操作——示例的 on_button_delete() 正是先 convert_iter_to_child_iter() 再对子模型 erase。erase 接受的就是迭代器；「排序模型只读」也不对，问题只在迭代器属于哪一层。",
         ref="排序：TreeModelSort 的迭代器须用 convert_iter_to_child_iter() 转回子模型"),
    dict(id="tv11-dd-1", page=DD, pos=2,
         stem="调了 m_TreeView.set_reorderable() 之后，用户能怎样移动行？",
         right="只能在这个 TreeView 内部拖动换位",
         wrong=["能拖到别的窗口，GTK 会自动搬运行数据",
                "能拖到桌面或文件管理器，把行导出成文件",
                "什么都不能拖，它开启的是列标题的换位功能"],
         why="原文：set_reorderable() 让条目能在 TreeView 自身之内移动（TreeStore 示例演示），但不提供「哪些条目可拖、能放到哪」的控制——要那种控制，就派生 TreeStore/ListStore 并覆盖 row_draggable_vfunc()/row_drop_possible_vfunc()。列标题换位是另一个调用（column->set_reorderable()），别混。",
         ref="Drag and Drop：set_reorderable() 只在自身内移动，细控要覆盖模型的拖放 vfunc"),
    dict(id="tv11-cm-1", page=CM, pos=1,
         stem="弹出菜单示例里这几行在做什么？",
         code="""
auto refGesture = Gtk::GestureClick::create();
refGesture->set_button(GDK_BUTTON_SECONDARY);
refGesture->signal_pressed().connect(
  sigc::mem_fun(*this, &TreeView_WithPopup::on_popup_button_pressed));
add_controller(refGesture);""",
         right="识别鼠标右键按下，作为弹出菜单的时机",
         wrong=["识别左键单击，用来选中被点击的那一行数据",
                "识别双击手势，行被激活时才弹出菜单",
                "识别任意按键按下，连键盘按键也一起响应"],
         why="原文：TreeView 的右键弹出菜单与普通弹出菜单做法基本一样，用 Gtk::GestureClick 检测鼠标点击。示例把按钮设为 GDK_BUTTON_SECONDARY（通常是右键），signal_pressed 的处理函数里 set_pointing_to() 定位、popup() 弹出 PopoverMenu。GestureClick 只管鼠标，不响应键盘。",
         ref="Popup Context Menu：用 Gtk::GestureClick 检测鼠标点击"),
    dict(id="tv11-ex-1", page=EX, pos=3,
         stem="editable_cells 示例的「validated (<10)」列是唯一不用 *_editable 方法加的列。输入的值要校验合格才进模型，它是怎么做的？",
         code="""
m_cellrenderer_validated.property_editable() = true;
m_cellrenderer_validated.signal_edited().connect(...);
// cellrenderer_validated_on_edited()（节选）：
int new_value = strtol(new_text.c_str(), &pchEnd, 10);
if(new_value >= 10)
{ /* show error dialog, restart editing */ }
else
  row[m_Columns.m_col_number_validated] = new_value;""",
         right="普通方法加列，自己设 editable、连 edited 信号，回调里校验合格才写入",
         wrong=["改用 append_column_editable()，编辑结果本来就不会自动进模型",
                "仍用 append_column_editable()，事后在 changed 里把值改回去",
                "不设 property_editable()，默认就地编辑但写入前会弹窗询问"],
         why="原文：editable 系列方法会把编辑出的新值立即存进模型；若要先校验（比如只收小于 10 的数），就用普通的 append_column() 加列，自己把 renderer 的 editable 属性设为 true、连接 signal_edited()，在处理函数里检查新值，合适才存。示例对不小于 10 的输入弹 MessageDialog 并让用户重输。",
         ref="The View 与 Editable Cells 示例：普通加列、edited 信号里校验后再存储"),
]

CHECKPOINT = [
    dict(id="tv11-cp-1", pos=0, locator="官方节页 sec-treeview-model",
         stem="（综合）同一份数据要以两种视图同时显示、各自可编辑，本章的做法是？",
         right="两个 TreeView 共用一个 TreeModel，各加自己的列",
         wrong=["数据复制两份各配一个模型，编辑时互相拷贝同步",
                "一个 TreeView 显示，另一个定时读它的内容自己重画",
                "做不到：一个 TreeModel 只能关联一个 TreeView"],
         why="Model/View 分离正为此设计：原文说同一个 TreeModel 可以被多个 TreeView 使用，同一底层数据可同时以两种方式显示与编辑，或两个视图显示同一 Model 的不同列——就像两条 SQL 查询查同一张表。编辑经由模型生效，天然同步，不需要互相拷贝；只想给行带额外数据时，加为模型列但不加到视图即可。",
         ref="综合 The Model：一个 TreeModel 可被多个 TreeView 使用"),
    dict(id="tv11-cp-2", pos=3, locator="本章开头的弃用说明与 chapter-listmodel 的 sec-listmodel-trees",
         stem="（综合）新代码要做列表或树形视图，本章开头特别标注了什么？",
         right="TreeView 已弃用：新代码列表用 ListView、表格用 ColumnView",
         wrong=["TreeView 仍是首选部件，ListView 只为超大数据量准备",
                "弃用的只是 C API，gtkmm 的 C++ 封装不受影响",
                "新列表体系做不了树形，树形场景仍必须用 TreeView"],
         why="本章开头即注明：TreeView 自 gtkmm 4.10 起弃用，新代码里列表用 Gtk::ListView、表格式列表用 Gtk::ColumnView。chapter-listmodel 一节补充：列表部件没有内建树形，仍要树形的话用 TreeListModel 把树拍平成列表、TreeExpander 部件负责展开收起。「弃用只是 C API」是误解——弃用就发生在 gtkmm 层面，本章因此通篇带弃用标注。",
         ref="综合本章开头的弃用说明与 chapter-listmodel 的 sec-listmodel-trees"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
