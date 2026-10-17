import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

DM, LN, CV, AR, TX, IM = (
    "sec-cairo-drawing-model",
    "sec-cairo-drawing-lines",
    "sec-cairo-curved-lines",
    "sec-cairo-drawing-arcs",
    "sec-drawing-text",
    "sec-draw-images",
)

INPAGE = [
    dict(id="da18-dm-1", page=DM, pos=1,
         stem="DrawingArea 第一次显示或被遮挡后又露出时，谁负责把它画出来？",
         right="你用 set_draw_func() 登记的绘制函数",
         wrong=["DrawingArea 内置默认绘制，会自动重画空白表面",
                "Gtk::Application 统一重绘所有窗口，不必登记绘制函数",
                "只有在构造函数里手动 stroke() 一次，以后就不用再画"],
         why="原文：多数部件自带重绘代码，DrawingArea 没有；需用 set_draw_func() 设置绘制函数，在首次显示或遮挡后再露出时由它决定如何画内容。",
         ref="The Cairo Drawing Model：set_draw_func() 与 DrawingArea 无内置绘制"),
    dict(id="da18-dm-2", page=DM, pos=0,
         stem="Cairo 绘图的基本模型是怎样的？",
         right="先定义不可见路径，再 stroke 或 fill 才可见",
         wrong=["每次 move_to / line_to 立刻把像素画到屏幕上",
                "只能先 fill 实心色块，不能用 stroke 描边路径",
                "路径一建好就永久保留，stroke 之后还会叠在上面"],
         why="原文：基本概念是定义「不可见」路径，再用 stroking 或 filling 让它们可见。stroke() 之后当前路径会被清掉（除非用 _preserve 变体）。",
         ref="The Cairo Drawing Model：invisible paths → stroke/fill"),
    dict(id="da18-ln-1", page=LN, pos=2,
         stem="默认坐标系下，下面这段在窗口里会画出怎样的线？",
         code="""
cr->move_to(0, 0);
cr->line_to(100, 100);
cr->stroke();""",
         right="从左上角斜向右下的一条线",
         wrong=["从左下角斜向右上（常见数学坐标那样）",
                "只抬笔移动，line_to 不会留下任何痕迹",
                "编译失败：必须先 scale() 才能用绝对坐标"],
         why="原文：原点在窗口左上角，正 x 向右、正 y 向下。move_to 抬笔不画线，line_to 建路径，stroke() 才描可见线。不是数学课本那种 Y 向上。",
         ref="Drawing Straight Lines：坐标系；move_to / line_to / stroke"),
    dict(id="da18-ln-2", page=LN, pos=3,
         stem="奇数像素宽的细线发糊时，示例用什么办法「定到像素中间」？",
         code="""
void MyArea::fix_lines(bool fix)
{
  m_fix = fix ? 0.5 : 0.0;
  queue_draw();
}""",
         right="把横坐标偏移 0.5 再 move_to / line_to",
         wrong=["把线宽改成 2.0，奇数宽就不会模糊",
                "调用 set_antialias(NONE) 关掉抗锯齿即可",
                "改用 rel_line_to，相对坐标天然对齐像素"],
         why="原文：奇数像素宽时若落在像素交界，Cairo 会向两侧各画半像素而糊掉；诀窍是把位置定在目标像素中间。示例用 m_fix=0.5，并 queue_draw() 强制重绘。",
         ref="Drawing thin lines：像素中间；thin_lines 示例 m_fix"),
    dict(id="da18-cv-1", page=CV, pos=1,
         stem="下面 curve_to 调用里，最后一对 (x3,y3) 表示什么？",
         code="""
cr->move_to(x0, y0);
cr->curve_to(x1, y1, x2, y2, x3, y3);""",
         right="曲线终点（目标点）",
         wrong=["起点控制点；终点其实是 move_to 的 (x0,y0)",
                "终点控制点；目标点要再调一次 line_to",
                "整条曲线的中点，用来决定弯曲程度"],
         why="原文：第一对坐标是起点控制点，第二对是终点控制点，最后一对是目标点（终点）。起点本身由之前的 move_to 给出。",
         ref="Drawing Curved Lines：curve_to 三组坐标的含义"),
    dict(id="da18-ar-1", page=AR, pos=0,
         stem="默认变换下，arc() 的角度为何「顺时针」增加？",
         code="""
cr->arc(xc, yc, r, 0.0, 2.0 * M_PI);""",
         right="0 朝 +X，M_PI/2 朝 +Y，而 +Y 向下",
         wrong=["Cairo 故意反转数学惯例，与 Y 轴方向无关",
                "角度用度数且从正北起算，所以看起来顺时针",
                "只有 arc_negative 才顺时针，arc 本身是逆时针"],
         why="原文：0 朝用户空间 +X，M_PI/2 朝 +Y；角度从 +X 转向 +Y 增加。默认矩阵下 +Y 向下，故角度顺时针增加。画整圆用 0 到 2π；反向用 arc_negative。",
         ref="Drawing Arcs and Circles：弧度、顺时针与 Y 向下"),
    dict(id="da18-tx-1", page=TX, pos=2,
         stem="在 DrawingArea 里用 Pango 画「Hi there!」时，最后一步通常是？",
         code="""
auto layout = create_pango_layout("Hi there!");
layout->set_font_description(font);
layout->get_pixel_size(text_width, text_height);
cr->move_to((w - text_width) / 2, (h - text_height) / 2);
/* ？ */""",
         right="layout->show_in_cairo_context(cr)",
         wrong=["cr->show_text(\"Hi there!\")，绕过 Layout 直接画",
                "layout->paint(cr)，Pango::Layout 的成员就是它",
                "Gtk::Label::set_text，把字符串交给标签部件显示"],
         why="原文：用 create_pango_layout() 建 Layout，改文本/字体后，用 Pango::Layout::show_in_cairo_context() 渲染。位置用 get_pixel_size() 量出的文字尺寸算出，再 move_to。",
         ref="Drawing Text with Pango：create_pango_layout + show_in_cairo_context"),
    dict(id="da18-im-1", page=IM, pos=3,
         stem="官方示例把图片画到 DrawingArea 正中时，关键两步是？",
         code="""
Gdk::Cairo::set_source_pixbuf(cr, m_image,
  (width - m_image->get_width()) / 2,
  (height - m_image->get_height()) / 2);
/* 画整张图 */""",
         right="接着调用 cr->paint()",
         wrong=["接着只调 stroke()，paint 只用于纯色背景",
                "set_source_pixbuf 是 Context 成员，写成 cr->set_source_pixbuf",
                "每次 on_draw 里必须 create_from_file，不能缓存 Pixbuf"],
         why="原文：用 Gdk::Cairo::set_source_pixbuf()（非 Context 成员）设源，再 paint() 画整图，或 rectangle+fill 画局部。示例在构造里 create_from_resource 缓存 m_image；文中提醒不要每次 draw 都加载文件。",
         ref="Drawing Images：set_source_pixbuf + paint；示例缓存 Pixbuf"),
]

CHECKPOINT = [
    dict(id="da18-cp-1", pos=1, locator="官方节页 sec-drawing-clock-example",
         stem="Clock 构造里连上 1000ms 超时后，on_timeout 每次被调时主要做什么？",
         code="""
bool Clock::on_timeout()
{
  queue_draw();
  return true;
}""",
         right="queue_draw() 使钟面失效重绘，并返回 true",
         wrong=["直接在超时槽里 stroke 指针，不必再进 on_draw",
                "返回 false，让超时只触发一次就永久断开连接",
                "调用 app->quit()，每秒重启一次整个事件循环"],
         why="原文：构造函数把 on_timeout 连到 1 秒超时；该函数唯一职责是让窗口失效，迫使 gtkmm 重绘。返回 true 表示继续周期性调用；实际画针在 on_draw。",
         ref="Clock 示例：signal_timeout + queue_draw + 返回 true"),
    dict(id="da18-cp-2", pos=2, locator="官方节页 sec-cairo-drawing-arcs 与 sec-cairo-drawing-model",
         stem="要画以 (ex,ey) 为中心、宽 ew 高 eh 的椭圆，推荐顺序是？",
         code="""
context->save();
context->translate(ex, ey);
context->scale(ew / 2.0, eh / 2.0);
context->arc(0.0, 0.0, 1.0, 0.0, 2 * M_PI);
context->restore();""",
         right="先 save，再平移缩放，arc 单位圆，最后 restore",
         wrong=["先 arc 大圆，再 scale，否则圆心会跑出窗口",
                "不必 save/restore，scale 会在 stroke 后自动还原",
                "椭圆必须用专用 ellipse()，arc 只能画正圆"],
         why="原文椭圆写法：save → translate 到中心 → 按半宽半高 scale → arc(0,0,1,0,2π) → restore。弧、圆、椭圆都用 arc()；save/restore 保证状态可嵌套还原。",
         ref="综合 Arcs 椭圆示例与 Drawing Model 的 save/restore"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
