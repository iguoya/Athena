import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

BUF, ANC, EX = "sec-textview-buffer", "sec-widgets-and-childanchors", "sec-textview-examples"

INPAGE = [
    dict(id="tx14-buf-1", page=BUF, pos=0,
         stem="关于 TextView 与 TextBuffer 的分工与复用，本章的说法是？",
         right="TextBuffer 是模型，多个 TextView 可共享同一个",
         wrong=["文字数据存在 TextView 里，TextBuffer 只是导出时的副本",
                "一个 TextBuffer 只能配一个 TextView，要多视图就得复制数据",
                "TextBuffer 管显示，TextView 管存放与编辑文字"],
         why="TextView 与 TreeView 一样是模型/视图设计：TextBuffer 是存放文字数据的模型。两个以上 TextView 可以共享同一个 TextBuffer（并可以让它们显示得稍有不同），也可以维护几个 TextBuffer、让同一个 TextView 在不同时间分别显示。",
         ref="The Buffer：TextBuffer 是模型，两个以上 TextView 可共享同一个"),
    dict(id="tx14-buf-2", page=BUF, pos=2,
         stem="程序在缓冲区里存了一个 iterator，随后用户在缓冲区里敲字删字。之后还拿这个旧 iterator 用，会怎样？",
         right="已失效：这类修改使迭代器作废，存位置要用 Mark",
         wrong=["仍有效：迭代器会自动跟着文字增删挪动，始终指在原位",
                "仍有效，但指向新敲入的第一个字符，得手动校正回原处",
                "编译期就报错：迭代器一旦过期，再写它编译不过"],
         why="原文写明：只要缓冲区被以影响字符数的方式修改，所有现存的迭代器都会失效，所以迭代器不能用来跨修改保存位置；要保存位置得用 Gtk::TextBuffer::Mark。「迭代器自动跟着挪」「编译期检查出来」都不是 GTK 的机制。",
         ref="Iterators：影响字符数的修改使现存迭代器全部失效，保存位置用 Mark"),
    dict(id="tx14-buf-3", page=BUF, pos=3,
         stem="文字已经在缓冲区里了，现在要把其中一段染成橙色背景，该用哪个调用？",
         code="""
auto refTagMatch = Gtk::TextBuffer::Tag::create();
refTagMatch->property_background() = "orange";""",
         right="apply_tag()：把标签应用到迭代器指定的这段区域",
         wrong=["insert_with_tag()：那是插入新文字时才用的",
                "给 TextBuffer 设 property_background()：背景属性在 Tag 上",
                "set_text() 重写这段文字，颜色会跟着字符一起存进缓冲区"],
         why="原文给了两条路：对已在缓冲区里的文字，用 apply_tag() 把标签应用到一段区域（区域两端用迭代器指定）；插入时就带上格式才用 insert_with_tag()。橙色背景是 Tag 的 property_background，不是 TextBuffer 或 TextView 的属性。",
         ref="Applying Tags：apply_tag() 应用到迭代器指定的区域；insert_with_tag() 是插入时指定"),
    dict(id="tx14-buf-4", page=BUF, pos=1,
         stem="光标（插入点）在 TextBuffer 里是怎么表示的？",
         right="内置 Mark（insert），用 get_insert() 访问",
         wrong=["一个内置 iterator：缓冲区为光标常驻一个迭代器",
                "TextView 的属性，记录着行号和列号",
                "一个内置 Tag，光标闪烁是它的渲染效果"],
         why="原文说缓冲区有两个内置 Mark——insert 与 selection_bound，分别用 get_insert() 和 get_selection_bound() 访问；光标就是 insert 这个 Mark，要用时再经 get_iter() 取它的迭代器。迭代器存不住位置（会失效），行号列号与 Tag 都不是光标的表示。",
         ref="Marks：内置 Mark 有 insert 与 selection_bound，经 get_insert() 等访问"),
    dict(id="tx14-anc-1", page=ANC, pos=1,
         stem="要把一个按钮嵌进文本中间。关于这两行，哪项说法是对的？",
         code="""
auto refAnchor = refBuffer->create_child_anchor(iter);
m_TextView.add_child_at_anchor(m_Button, refAnchor);""",
         right="锚由 buffer 建，部件由 view 挂到锚上",
         wrong=["两行都该调在 view 上，buffer 只管文字不管锚",
                "两行都该调在 buffer 上，显示部件本来就是缓冲区的职责",
                "顺序无所谓，先把部件挂上、再建锚也一样"],
         why="原文的流程就是两步：先 Gtk::TextBuffer::create_child_anchor() 在指定位置（迭代器处）建 ChildAnchor——锚属于缓冲区；再 Gtk::TextView::add_child_at_anchor() 把部件挂到这个锚上——摆放部件是视图的事。这正是本章模型/视图分工的延伸。",
         ref="Widgets 与 ChildAnchor：create_child_anchor() 在 buffer 上，add_child_at_anchor() 在 view 上"),
    dict(id="tx14-ex-1", page=EX, pos=2,
         stem="按官方示例，构造函数末尾是 fill_buffers(); on_button_buffer1();。窗口刚显示时，TextView 里是哪段文字？",
         code="""
void ExampleWindow::fill_buffers()
{
  m_refTextBuffer1 = Gtk::TextBuffer::create();
  m_refTextBuffer1->set_text("This is the text from TextBuffer #1.");
  m_refTextBuffer2 = Gtk::TextBuffer::create();
  m_refTextBuffer2->set_text(
      "This is some alternative text, from TextBuffer #2.");
}""",
         right="#1 那段：on_button_buffer1() 已切换视图",
         wrong=["空白：两个缓冲区还没 set_buffer() 给视图，要先点按钮",
                "#2 那段：视图自动显示最近创建的那个缓冲区",
                "空白：TextView 只认它自己默认创建的缓冲区"],
         why="fill_buffers() 只是创建并填充两个 TextBuffer；显示哪个由 set_buffer() 决定，on_button_buffer1() 里正是 m_TextView.set_buffer(m_refTextBuffer1)。构造函数末尾调了它，所以一打开就是 buffer1 的文字；点 Use buffer 2 才会切到另一段。",
         ref="Examples：fill_buffers() 之后构造函数末尾调 on_button_buffer1()，set_buffer() 切换"),
]

CHECKPOINT = [
    dict(id="tx14-cp-1", pos=0, locator="官方节页 sec-textview-buffer（Iterators 与 Marks）",
         stem="缓冲区开头存了一个迭代器和一个 Mark，随后用户在缓冲区最前面敲入了 abcdef。稍后执行到最后一行时，情况是？",
         code="""
// iter 指向缓冲区开头
auto mark = refBuffer->create_mark(iter);
// ……用户在缓冲区最前面敲入了 abcdef……
auto iter2 = refBuffer->get_iter(mark);""",
         right="iter 作废；iter2 可用，取到 mark 当前的位置",
         wrong=["两个都作废：Mark 与迭代器一样怕文字修改",
                "两个都可用：迭代器自动挪到 abcdef 之后，Mark 原地不动",
                "编译失败：作废的迭代器不能再出现在后面的语句里"],
         why="在缓冲区最前面敲入 6 个字符是「影响字符数的修改」，原文写明这会让所有现存的迭代器失效，所以 iter 不可再用；Mark 正是为此准备的，文本变化后它仍然有效（会随编辑挪到新位置），稍后用 get_iter() 从它取回新的迭代器。",
         ref="综合 Iterators 与 Marks：迭代器跨修改失效，Mark 保存位置后经 get_iter() 取回"),
    dict(id="tx14-cp-2", pos=3, locator="官方节页 sec-textview-buffer（The View 与 Default formatting）",
         stem="两个 TextView 共享同一个 TextBuffer。给它们分别 set_left_margin(10) 与 set_left_margin(40)，显示会一样吗？",
         right="不一样：边距是单个视图的设置，同一缓冲区本就能各有显示",
         wrong=["一样：格式都在缓冲区里，两个视图必然同步",
                "一样：set_left_margin() 会写进缓冲区，后调的覆盖先调的",
                "不一样，但前提是给两个视图各复制一份缓冲区"],
         why="原文说 TextView 的 set_left_margin() 这类方法改变的是这个视图对缓冲区的呈现，共享同一缓冲区的多个 TextView 本来就可以显示得稍有不同，不需要复制缓冲区。要让某一段文字（而非整个视图）带格式，用的是缓冲区里的 Tag——Tag 若指定了同样的内容，还会盖过视图的默认设置。",
         ref="综合 The View 与 Default formatting：视图各自的呈现设置，Tag 可覆写"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
