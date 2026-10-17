import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

FM, CO, PA, EX = (
    "sec-clipboard-formats",
    "sec-clipboard-copy",
    "sec-clipboard-paste",
    "sec-clipboard-examples",
)

INPAGE = [
    dict(id="cl20-fm-1", page=FM, pos=1,
         stem="应用里要拿到剪贴板实例，原文推荐的入口是？",
         right="get_clipboard()",
         wrong=["只能自己 new Gdk::Clipboard，再手动挂到顶级窗口上使用",
                "必须先创建 DragSource，因为剪贴板只是拖放 API 的别名",
                "只能从 Gtk::Application::create 返回的 RefPtr 里间接取用"],
         why="原文：用 Gtk::Widget::get_clipboard() 或 Gdk::Display::get_clipboard() 取得剪贴板实例。拖放与剪贴板共用格式机制，但不是同一套对象创建路径。",
         ref="Formats：get_clipboard() 两个入口"),
    dict(id="cl20-fm-2", page=FM, pos=0,
         stem="Copy 与 Paste 之间往往隔很久。Gdk::Clipboard 如何避免阻塞等待？",
         right="多数方法吃 sigc::slot，就绪后再回调",
         wrong=["调用方必须自旋轮询，直到数据准备好才返回",
                "只能在同一个 clicked 槽里同步读写，否则会丢数据",
                "必须开第二个线程阻塞读，主循环里禁止碰剪贴板"],
         why="原文：应用不必在 Copy 与 Paste 之间空等；许多 Gdk::Clipboard 方法接受 sigc::slot，就绪时再回调并提供数据。",
         ref="Formats：异步回调（slot）"),
    dict(id="cl20-co-1", page=CO, pos=2,
         stem="用户点 Copy 时，下面这行实际做了什么？",
         code="""
void ExampleWindow::on_button_copy()
{
  get_clipboard()->set_text("example_custom_target");
}""",
         right="把这段文本写入剪贴板",
         wrong=["只登记 MIME 名，真正数据要等 Paste 才去读文件",
                "启动拖放会话，因为 set_text 属于 DragSource API",
                "清空剪贴板：参数只是调试标签，不会被粘贴"],
         why="原文 Copy 节：用户要求复制时，把数据写到 Clipboard；示例正是 get_clipboard()->set_text(...)。这不是拖放 API，参数就是要放入的文本。",
         ref="Copy：set_text 写入剪贴板"),
    dict(id="cl20-pa-1", page=PA, pos=3,
         stem="Paste 按钮这样写，数据实际在哪一步到手？",
         code="""
void ExampleWindow::on_button_paste()
{
  get_clipboard()->read_text_async(sigc::mem_fun(*this,
              &ExampleWindow::on_clipboard_received));
}
void ExampleWindow::on_clipboard_received(
    Glib::RefPtr<Gio::AsyncResult>& result)
{
  auto text = get_clipboard()->read_text_finish(result);
}""",
         right="finish 时拿到",
         wrong=["read_text_async 一返回，text 就已经在局部变量里了",
                "必须先 get_formats()，否则 finish 会永远失败",
                "finish 只能在另一线程调用，主线程调用会断言"],
         why="原文：Paste 时请求特定格式并提供回调；回调里用 read_text_finish(result) 取文本。async 只是发起请求；get_formats 用于探测可用格式，不是 finish 的前提。",
         ref="Paste：read_text_async + read_text_finish"),
    dict(id="cl20-ex-1", page=EX, pos=1,
         stem="Ideal 示例相对 Simple，多做了哪件与粘贴按钮相关的事？",
         right="听 changed，不可用则禁 Paste",
         wrong=["改用同步 read_text，并去掉全部 AsyncResult 回调路径",
                "不再支持 text/plain，只保留自定义二进制图像格式",
                "禁止多实例：Application 去掉 NON_UNIQUE 标志位"],
         why="原文 Ideal：定义自定义 clipboard target（格式仍是文本）；并用 Gdk::ContentFormats::signal_changed()，在剪贴板没有可用格式时禁用 Paste。Simple 的问题正是未标识特定类型。",
         ref="Examples Ideal：signal_changed 与禁用 Paste"),
]

CHECKPOINT = [
    dict(id="cl20-cp-1", pos=2, locator="官方节页 sec-clipboard-examples",
         stem="Simple 示例的 main 为何给 Application 加上 NON_UNIQUE？",
         code="""
auto app = Gtk::Application::create(
  "org.gtkmm.example", Gio::Application::Flags::NON_UNIQUE);""",
         right="允许同时开多个实例，方便跨窗口粘贴自测",
         wrong=["NON_UNIQUE 会关闭剪贴板，避免与系统剪贴板冲突",
                "没有该标志就无法调用 get_clipboard()",
                "该标志专门打开 Drag and Drop，与剪贴板无关"],
         why="示例注释：用 NON_UNIQUE 是因为应该能同时运行本应用的多个实例。它不关闭剪贴板，也不是 get_clipboard 的前提。",
         ref="综合 Examples：NON_UNIQUE 多实例自测"),
    dict(id="cl20-cp-2", pos=0, locator="官方节页 sec-clipboard-formats 与 sec-clipboard-examples",
         stem="本章说拖放与剪贴板应共用什么？Simple 示例在格式上的缺点是？",
         right="共用同一套数据格式；Simple 未标识特定类型",
         wrong=["必须各用各的 MIME；Simple 错在用了 text/plain",
                "剪贴板只能走 XML，拖放只能走二进制，Simple 混用了",
                "两者 API 完全独立，Simple 却错误地复用了 ContentFormats"],
         why="Formats 节：拖放与剪贴板用同一机制，建议两边用同一数据格式。Simple 示例说明：用标准文本虽简单，但不理想，因为没有把 Clipboard 数据标识成特定类型；Ideal 才定义自定义 target。",
         ref="综合 Formats + Examples：格式共用；Simple 缺类型标识"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
