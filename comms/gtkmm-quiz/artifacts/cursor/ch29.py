import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

TC, GD, EX = ("sec-the-constraints", "sec-using-glib-dispatcher",
              "sec-multithread-example")

INPAGE = [
    dict(id="mt29-tc-1", page=TC, pos=0,
         stem="gtkmm 多线程程序要特别小心，根本原因是什么？",
         right="libsigc++ 与 sigc::trackable 不是线程安全的",
         wrong=["glib 本身不是线程安全的，任何跨线程调用都会立刻崩溃",
                "只有 Cairo 绘图不安全，信号连接可以随便跨线程去做",
                "std::thread 与 gtkmm 互斥，官方禁止再创建第二个线程"],
         why="开篇写明：libsigc++ 尤其是 sigc::trackable 不是线程安全的，幕后交互没有互斥保护。下文规则 6 反而说 glib 自身是线程安全的，不安全的是走 libsigc++ 的 glibmm 封装。",
         ref="The constraints：开篇关于 libsigc++ / trackable 非线程安全"),
    dict(id="mt29-tc-2", page=TC, pos=1,
         stem="主 GUI 线程里给按钮连了槽。工作线程若直接 emit 该按钮的 clicked，违反哪条？",
         code="""
// 主线程：
m_button.signal_clicked().connect(
  sigc::mem_fun(*this, &Win::on_clicked));
// 工作线程：
m_button.signal_clicked().emit();  // ← 问题在这""",
         right="信号由创建线程拥有；只有该线程应 connect / emit",
         wrong=["只要槽函数里不加锁，跨线程 emit 就算合法操作",
                "clicked 是 GTK 内部信号，任意线程 emit 都安全",
                "只有 disconnect 必须同线程，emit 可以在工作线程做"],
         why="规则 2：sigc::signal 由创建线程拥有，只有该线程应 connect、emit/operator()、置空已连接的槽。gtkmm 部件的信号只应在主 GUI 线程操作。",
         ref="The constraints：规则 2（信号归属与 emit 线程）"),
    dict(id="mt29-ex-1", page=EX, pos=2,
         stem="示例里谁创建/销毁工作线程？共享的 fraction_done 等字段靠什么同步？",
         code="""
// Start work 按下时：
m_WorkerThread = new std::thread([this] { m_Worker.do_work(this); });
// ExampleWorker 成员：m_Mutex、m_fraction_done、m_message …""",
         right="GUI 线程创建并 join；字段用 std::mutex 串行化",
         wrong=["工作线程自己 new 自己，GUI 只负责点按钮看进度条",
                "不需要锁：Dispatcher::emit 会自动把字段拷到主线程",
                "用 sigc::connection 当锁，connect 成功后再读写共享字段"],
         why="示例：按 Start 时在 GUI 线程 new std::thread；结束或 Stop/Quit 时 GUI 侧 join 再 delete。ExampleWorker 的共享数据用 mutex；Dispatcher 只传「有通知」，不代替数据同步。",
         ref="Example：两线程分工、mutex 保护共享数据、仅 GUI 更新界面"),
    dict(id="mt29-gd-1", page=GD, pos=3,
         stem="Glib::Dispatcher 与普通 sigc::signal 在「槽在哪个线程执行」上有何不同？",
         code="""
// 主 GUI 线程构造并 connect：
Glib::Dispatcher m_Dispatcher;
m_Dispatcher.connect(sigc::mem_fun(*this, &Win::on_notify));
// 工作线程：
m_Dispatcher.emit();""",
         right="槽在构造 Dispatcher 的线程跑，不在 emit 线程",
         wrong=["两者一样：槽都在调用 emit() 的那个线程里执行",
                "Dispatcher 的槽在任意空闲线程执行，由运行时挑选",
                "只有工作线程 emit 时槽才跑；接收者自己 emit 会被忽略"],
         why="原文对比：sigc::signal 的槽在 emit/operator() 的线程执行；Dispatcher 相反，槽在构造 Dispatcher 的线程（须有 glib 主循环）执行。工作线程 emit 即可让主线程安全跑 gtkmm。",
         ref="Using Glib::Dispatcher：开篇对比 signal 与 Dispatcher 的执行线程"),
    dict(id="mt29-gd-2", page=GD, pos=0,
         stem="工作线程要把计算结果交给 GUI 更新标签。只用 Dispatcher::emit() 够不够？缺什么？",
         right="不够：Dispatcher 不能传参数，数据要用异步队列",
         wrong=["够：emit 可以带任意参数包，槽函数里直接解包就能用",
                "够：槽的返回值会自动传回工作线程，正好用来同步进度",
                "不够：应改用 sigc::signal<void(int)> 让工作线程直接 emit 带参"],
         why="原文：Dispatcher 类似 signal<void()>，不能传未绑定参数、不能返回值；传数据最好用线程安全（异步）队列。工作线程直接 emit 带参的 gtkmm/sigc 信号又会撞上约束节的规则。",
         ref="Using Glib::Dispatcher：无未绑定参数/返回值；用异步队列传数据"),
]

CHECKPOINT = [
    dict(id="mt29-cp-1", pos=1, locator="官方节页 sec-multithread-example 与 sec-using-glib-dispatcher",
         stem="示例里工作线程调用 notify() 之后，谁更新 ProgressBar？共享数据怎么护？",
         code="""
void ExampleWindow::notify()
{
  m_Dispatcher.emit();  // 在工作线程里调用
}
void ExampleWindow::on_notification_from_worker_thread()
{
  // ……
  update_widgets();  // 内含 m_ProgressBar.set_fraction(...)
}""",
         right="主 GUI 在 Dispatcher 槽里更新；共享数据用 std::mutex 保护",
         wrong=["工作线程在 notify() 里直接 set_fraction，Dispatcher 只打日志",
                "两个线程都可以改 ProgressBar，靠 GTK 内部队列自动合并",
                "不需要锁：Glib::ustring 与 double 的读写本身就是原子的"],
         why="示例说明：Dispatcher 把通知送到 GUI 线程；ExampleWorker 的共享数据用 mutex；只有 GUI 线程更新 GUI。notify() 仅 emit，真正改 ProgressBar/TextView 在 on_notification_from_worker_thread → update_widgets。",
         ref="综合 Example：Dispatcher 通知、mutex、仅 GUI 更新界面"),
    dict(id="mt29-cp-2", pos=2, locator="官方节页 sec-the-constraints",
         stem="对象派生自 sigc::trackable。线程 A 已用 mem_fun 为它建过槽。线程 B 若再 mem_fun 同一对象或把槽拷走，违反哪条？",
         right="规则 4/5：此类槽勿跨线程拷贝/销毁；首建槽的线程独占后续 mem_fun",
         wrong=["规则 1：只能用 Dispatcher，任何 mem_fun 在多线程程序里都非法",
                "规则 3：connection 对象可以跨线程，槽对象反而没有归属限制",
                "规则 6：glib 非线程安全，与 trackable / mem_fun 无关"],
         why="规则 4：引用 trackable 方法的 mem_fun 槽不得拷到其它线程、也不得由创建线程以外销毁。规则 5：第一个创建此类槽的线程拥有该对象上后续一切 mem_fun / 置空。规则 1 是推荐用 Dispatcher 调 gtkmm；规则 6 说的是 glibmm 封装非线程安全，不是禁止 mem_fun。",
         ref="综合 The constraints：规则 4 与 5（trackable 与 mem_fun 槽归属）"),
]

if __name__ == "__main__":
    items = [build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT]
    report(items)
