import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

CC, CW, CSS = "sec-custom-containers", "sec-custom-widgets", "sec-custom-css-names"

INPAGE = [
    dict(id="cw28-cc-1", page=CC, pos=1,
         stem="直接从 Gtk::Widget 派生自定义容器时，文档要求覆写哪一组虚方法来控制子部件布局？",
         right="get_request_mode_vfunc、measure_vfunc、size_allocate_vfunc",
         wrong=["snapshot_vfunc、on_realize、on_unrealize（自绘用的那一组）",
                "on_map、on_unmap、size_allocate_vfunc（缺 measure 与 request mode）",
                "get_preferred_width / get_preferred_height（gtkmm3 旧尺寸 API）"],
         why="原文列出自定义容器应覆写 get_request_mode_vfunc()、measure_vfunc()、size_allocate_vfunc()——三者控制子部件布局。snapshot/on_realize 等属于自绘部件；get_preferred_* 是旧 API，本章以 measure_vfunc 为准。",
         ref="Custom Containers：直接从 Gtk::Widget 派生时应覆写的虚方法列表"),
    dict(id="cw28-cc-2", page=CC, pos=0,
         stem="托管的自定义容器若不在 C 对象终结前解除子部件父子关系，运行时最可能看到什么？",
         code="""
// MyContainer 用 Gtk::make_managed 放进父容器；
// 析构里若 gobj() 已为空则直接 return，且从未连接 signal_destroy
MyContainer::~MyContainer()
{
  if (!gobj())
    return;
  // ……未 unparent 子部件
}""",
         right="Gtk 警告：…still has children left",
         wrong=["编译失败：托管容器在语法上就不允许再挂任何子部件",
                "静默泄漏：子部件永远留在内存，运行期却完全没有任何警告",
                "自动 unparent：Gtk::Widget 基类析构会清掉全部子部件"],
         why="原文：容器必须在底层 C 对象终结前 unparent 子部件。托管时 signal_destroy 处理函数会跑，析构时 gobj() 往往已空，只靠析构会漏掉——示例注释正是这条 Finalizing … children left 警告。",
         ref="Custom Containers：终结前 unparent；托管用 signal_destroy（gtkmm 4.8+）"),
    dict(id="cw28-cc-3", page=CC, pos=2,
         stem="get_request_mode_vfunc() 返回 HEIGHT_FOR_WIDTH 之后，关于 measure_vfunc() 哪项正确？",
         right="仍须对合理输入都返回说得通的值；所请求模式不保证兑现",
         wrong=["GTK 保证永远按 HEIGHT_FOR_WIDTH 来问，其它分支可随便返回 0",
                "可以不实现 measure_vfunc，基类会按你请求的模式自动量尺寸",
                "只需实现「问高度」的分支，「问宽度」时直接返回 -1 即可"],
         why="原文：你无法保证得到所请求的 SizeRequestMode，因此 measure_vfunc() 必须对所有合理输入返回合适值。请求模式只是偏好，不是契约。",
         ref="Custom Containers：measure_vfunc 须覆盖合理输入；模式不保证"),
    dict(id="cw28-cw-1", page=CW, pos=3,
         stem="下面 snapshot_vfunc 里，真正开始在部件上作画的一步是哪句？",
         code="""
void MyWidget::snapshot_vfunc(const Glib::RefPtr<Gtk::Snapshot>& snapshot)
{
  const auto allocation = get_allocation();
  const Gdk::Rectangle rect(0, 0, allocation.get_width(), allocation.get_height());
  auto cr = snapshot->append_cairo(rect);
  Gdk::Cairo::set_source_rgba(cr, m_background);
  Gdk::Cairo::add_rectangle_to_path(cr, rect);
  cr->fill();
  // ……再用 cr 描前景
}""",
         right="append_cairo(rect) 取得上下文，再 fill",
         wrong=["get_allocation() 一调用就开始绘制，后面的 cr 只是装饰",
                "必须先 new Cairo::Context，再交给 snapshot 去登记",
                "只调 set_source_rgba 就会画完，fill 完全可以省略"],
         why="原文：snapshot_vfunc 创建渲染节点（例如 Cairo::Context 节点）并在其上绘制。示例用 snapshot->append_cairo(rect) 取得 cr，再 set_source / fill / stroke。get_allocation 只取尺寸；没有 fill/stroke 不会落墨。",
         ref="Custom Widgets：snapshot_vfunc 与官方 Penrose 示例的 append_cairo"),
    dict(id="cw28-cw-2", page=CW, pos=1,
         stem="从 Gtk::Widget 直接派生自绘部件时，下面哪项关于虚方法「是否必覆写」符合原文？",
         right="measure 与 snapshot 应覆写，on_realize 等可选",
         wrong=["所列虚方法一律必覆写，否则自定义部件根本无法显示",
                "只需覆写 on_draw()（gtkmm3 习惯），GTK4 已不再用 snapshot",
                "只有 get_request_mode_vfunc 必覆写，其余虚方法全可省略"],
         why="原文表格：measure_vfunc、snapshot_vfunc 未标 optional；get_request_mode、size_allocate、on_realize/unrealize、on_map/unmap 标 optional，基类方法常已够用。自绘靠 snapshot_vfunc，不是旧的 on_draw。",
         ref="Custom Widgets：应覆写的虚方法列表（含 optional 标注）"),
    dict(id="cw28-css-1", page=CSS, pos=0,
         stem="示例里三种「从部件指向 CSS 数据」的做法分别对应哪组调用？",
         code="""
// MyButton 经 ExtraClassInit 调 gtk_widget_class_set_css_name(..., "my-button")
m_Label_Child1.set_name("my-label1");
m_Label_Child2.add_css_class("my-label2");""",
         right="类级 CSS 节点名；实例部件名（#）；实例 CSS 类名（.）",
         wrong=["三者都只是实例名，CSS 选择器里一律写成 #xxx",
                "只能用 set_name；节点名与类名在 GTK4 里都已取消",
                "add_css_class 改的是 GType 名，set_name 才是加 CSS 类"],
         why="原文三种方式：gtk_widget_class_set_css_name（类 init，整类节点名）、set_name（实例名，CSS 用 #）、add_css_class/add_class_name（实例 CSS 类，用 .）。示例注释与 custom_gtkmm.css 正是 my-button / #my-label1 / .my-label2。",
         ref="Custom CSS Names：三种引用方式与示例构造函数注释"),
]

CHECKPOINT = [
    dict(id="cw28-cp-1", pos=2, locator="官方节页 sec-custom-containers 与 sec-custom-widgets",
         stem="父容器实际分给自定义部件的宽高，是在哪一步交给你的？多出来的空间怎么办？",
         right="size_allocate_vfunc 收到实际宽高，多余空间由你处理",
         wrong=["measure_vfunc 返回自然尺寸后，GTK 保证正好分那么多、不会多给",
                "on_realize 里读 Gdk 窗口尺寸即可，与布局虚方法完全无关",
                "snapshot_vfunc 参数里已带最终宽高，布局阶段不必再管分配"],
         why="容器节：size_allocate_vfunc 收到父容器决定的实际宽高，可能大于最小甚至自然尺寸；留白、扩展子部件或加大填充由你定。measure 只报告需求；snapshot 负责画，不代替分配。",
         ref="综合 Custom Containers：size_allocate_vfunc 与多余空间的处理"),
    dict(id="cw28-cp-2", pos=3, locator="官方节页 sec-custom-css-names 与 sec-custom-widgets",
         stem="要给自定义按钮类的所有实例设同一 CSS 节点名 my-button，正确做法是？",
         code="""
class MyButton : public MyExtraInit, public Gtk::Button {
  MyButton(...)
  : Glib::ObjectBase("MyButton"),
    MyExtraInit("my-button"),
    Gtk::Button(...)
  {}
};""",
         right="经 ExtraClassInit 在类 init 里设置 CSS 节点名",
         wrong=["在 C++ 构造函数里直接调用 gtk_widget_class_set_css_name",
                "对每个实例 set_name(\"my-button\")，效果与类节点名完全相同",
                "改掉 G_OBJECT_TYPE_NAME，CSS 就会自动用那个类型字符串"],
         why="gtk_widget_class_set_css_name 只能在类 init 调用，未包成 C++ 成员；示例用 ExtraClassInit。set_name 是实例名（# 选择器），不是类节点名；GType 显示名也不等于 CSS 节点名。",
         ref="综合 Class Init 与 Custom CSS Names：ExtraClassInit 示例"),
]

if __name__ == "__main__":
    items = [build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT]
    report(items)
