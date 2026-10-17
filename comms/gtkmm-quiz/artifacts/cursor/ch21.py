import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

PO, PS, RT, AS, PDF, PV, PD = (
    "sec-printoperation",
    "sec-page-setup",
    "sec-printing-rendering-text",
    "sec-async-printing-ops",
    "sec-printing-export-to-pdf",
    "sec-printing-preview",
    "sec-printing-printdialog",
)

INPAGE = [
    dict(id="pr21-po-1", page=PO, pos=1,
         stem="PrintOperation::run() 进入打印循环后，哪两个信号是你必须处理的？",
         right="begin_print 与 draw_page",
         wrong=["paginate 与 status_changed（其余都可选）",
                "done 与 end_print（用来创建 Pango::Layout）",
                "request_page_setup 与 create_custom_widget"],
         why="原文：begin_print 必须处理——在此用 PrintContext 创建并设置 Pango::Layout、分页；draw_page 也必须处理——按页号绘制。paginate、status_changed、request_page_setup 等按需。",
         ref="PrintOperation Signals：begin_print / draw_page 必处理"),
    dict(id="pr21-ps-1", page=PS, pos=0,
         stem="应用里弹出页面设置对话框，原文给出的做法是？",
         code="""
auto new_page_setup = Gtk::run_page_setup_dialog(
    *this, m_refPageSetup, m_refSettings);
m_refPageSetup = new_page_setup;""",
         right="run_page_setup_dialog 并保存 PageSetup",
         wrong=["只调 PrintOperation::run(PREVIEW)，设置会自动写回成员",
                "new Gtk::PageSetup 即可，对话框由 Display 全局弹出",
                "只能改 PrintSettings，PageSetup 不允许应用侧再保存"],
         why="原文：用 Gtk::run_page_setup_dialog() 得到 PageSetup；应保存所选设置，以便对话框再次打开时沿用，并用来更新 PrintOperation。",
         ref="Page Setup：run_page_setup_dialog 与保存"),
    dict(id="pr21-rt-1", page=RT, pos=2,
         stem="打印用的 Pango::Layout 应当怎样创建？",
         right="PrintContext::create_pango_layout()",
         wrong=["Pango::Layout::create() 后手动绑到任意 Cairo::Context",
                "Gtk::Label::get_layout()，把界面标签的布局直接拿去印",
                "new Pango::Layout，再 set_font_description 即可开印"],
         why="原文：打印用的 Pango::Layout 应通过 PrintContext::create_pango_layout() 创建；页指标用 get_width()/get_height()；draw_page 里再取 Cairo::Context 画 LayoutLine。",
         ref="Rendering text：create_pango_layout()"),
    dict(id="pr21-as-1", page=AS, pos=3,
         stem="调用 set_allow_async() 之后，run() 可能立刻返回什么？接下来靠什么收尾？",
         code="""
op->set_allow_async();
auto res = op->run(/* ... */);
// res 可能是 IN_PROGRESS""",
         right="IN_PROGRESS；听 done 等信号",
         wrong=["ERROR；异步模式下 run() 失败是唯一可能结果",
                "APPLY；表示已经打印完，不必再连接任何信号",
                "CANCEL；异步只用于用户点取消时的快捷路径"],
         why="原文：默认 run() 完成才返回；set_allow_async() 后可能返回 IN_PROGRESS，需实现 done 与 status_changed。并非所有平台支持 allow_async，但 done 仍会发出。",
         ref="Asynchronous operations：IN_PROGRESS 与 done/status_changed"),
    dict(id="pr21-pdf-1", page=PDF, pos=1,
         stem="不经过「打印到文件」对话框、直接从代码导出 PDF，应怎样写？",
         code="""
auto op = Gtk::PrintOperation::create();
// ...set up op...
op->set_export_filename("test.pdf");
auto res = op->run(Gtk::PrintOperation::Action::EXPORT);""",
         right="set_export_filename 再 run(EXPORT)",
         wrong=["只 set_export_filename，不必 run，文件会立刻写出磁盘",
                "run(Action::PRINT) 即可，导出文件名参数会被忽略掉",
                "必须先 run(PREVIEW)，预览窗口关闭后才会生成 PDF"],
         why="原文：对话框里的 Print to file 无需额外实现；若要从代码直接生成 PDF，set_export_filename 再 run(Action::EXPORT)。",
         ref="Export to PDF：set_export_filename + EXPORT"),
    dict(id="pr21-pv-1", page=PV, pos=2,
         stem="应用想直接进入预览（不先走打印对话框），应调用？",
         code="""
op->run(Gtk::PrintOperation::Action::PREVIEW, *this);""",
         right="run(Action::PREVIEW, 父窗口)",
         wrong=["run(Action::EXPORT)，系统会自动改成预览",
                "只能点原生对话框上的预览按钮，API 无法直接开预览",
                "set_allow_async() 一次，下次 run(PRINT) 就会变预览"],
         why="原文：原生对话框有预览按钮，也可从应用直接 run(Action::PREVIEW, *this)。Unix 默认用外部查看器，Windows 用原生预览；必要时可覆盖为自定义预览。",
         ref="Preview：Action::PREVIEW"),
    dict(id="pr21-pd-1", page=PD, pos=0,
         stem="Gtk::PrintDialog 从哪个 gtkmm 版本起可作为 PrintOperation 的替代？",
         right="gtkmm 4.14 起",
         wrong=["gtkmm 3.0 起就有，只是本章放在最后介绍",
                "gtkmm 4.0 起强制取代 PrintOperation",
                "尚未进入稳定版，示例里的宏永远为假"],
         why="原文：Since gtkmm 4.14，Gtk::PrintDialog 可作为 Gtk::PrintOperation 的替代；仍用同一套 PageSetup / PrintSettings，Cairo 与 Pango 渲染方式也相似。示例用 GTKMM_CHECK_VERSION(4,13,1) 门控。",
         ref="PrintDialog：自 gtkmm 4.14 起"),
]

CHECKPOINT = [
    dict(id="pr21-cp-1", pos=3, locator="官方节页 sec-printoperation 与 sec-printing-rendering-text",
         stem="Simple 示例把创建 Pango::Layout、分页放在哪？draw_page 做什么？",
         code="""
void PrintFormOperation::on_begin_print(
    const Glib::RefPtr<Gtk::PrintContext>& print_context)
{
  m_refLayout = print_context->create_pango_layout();
  // set font, width, text; compute m_PageBreaks; set_n_pages(...)
}
void PrintFormOperation::on_draw_page(
    const Glib::RefPtr<Gtk::PrintContext>& context, int page_nr)
{
  // get_cairo_context(); show LayoutLine for this page
}""",
         right="begin_print 建 Layout；draw_page 画",
         wrong=["两者都在 draw_page 里每次重建 Layout，begin_print 留空",
                "Layout 在构造函数里创建，begin_print 只许调用 set_n_pages",
                "draw_page 负责分页，begin_print 只负责弹出打印对话框"],
         why="原文强调：Pango::Layout 在 begin_print 里创建与分页；draw_page 用 PrintContext 取 Cairo::Context，迭代 begin_print 里建好的 Layout 画当前页。Simple 示例正是如此分工。",
         ref="综合 PrintOperation + Rendering + Examples Simple"),
    dict(id="pr21-cp-2", pos=1, locator="官方节页 sec-extending-print-dialog",
         stem="给打印对话框加自定义页，create_custom_widget 与 custom_widget_apply 各做什么？",
         code="""
Gtk::Widget* CustomPrintOperation::on_create_custom_widget()
{
  set_custom_tab_label("My custom tab");
  auto hbox = new Gtk::Box(Gtk::Orientation::HORIZONTAL, 8);
  // append label + m_Entry ...
  return hbox;
}
void CustomPrintOperation::on_custom_widget_apply(Gtk::Widget*)
{
  auto user_input = m_Entry.get_text();
}""",
         right="前者交回页内部件；后者读取用户输入",
         wrong=["前者读取输入；后者必须再 new 一套部件替换对话框",
                "两个信号都只改标题，真正的页内容由 PageSetup 提供",
                "只需 create_custom_widget，apply 在 gtkmm4 已删除"],
         why="原文两步：set_custom_tab_label + 在 create_custom_widget 返回容器部件；在 custom_widget_apply 里取数据。可把输入部件做成类成员以简化 apply。",
         ref="综合 Extending the print dialog：两信号分工"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
