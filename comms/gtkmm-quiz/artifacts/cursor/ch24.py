import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

TO, IO, ID = "sec-timeouts", "sec-monitoring-io", "sec-idle-functions"

INPAGE = [
    dict(id="tm24-to-1", page=TO, pos=1,
         stem="下面这个超时回调被 Glib::signal_timeout() 连上之后，会怎样？",
         code="""
bool MyCallback()
{
  std::cout << "Hello World!" << std::endl;
  return false;
}""",
         right="只调用一次：返回 false 会把这条超时连接断开",
         wrong=["每隔 interval 毫秒反复调用，因为超时一旦连上就不会停",
                "根本不会被调用：超时槽必须返回 void 才能登记成功",
                "调用一次后主循环立刻退出，整个程序随之结束"],
         why="原文：信号处理函数类型是 sigc::slot<bool()>，返回 false 就停止该超时方法；要反复调用必须返回 true。示例 MyCallback 返回 true 才会重复打印。返回 false 不是退出主循环。",
         ref="Timeouts：返回 false 停止超时；返回 true 才反复调用"),
    dict(id="tm24-to-2", page=TO, pos=0,
         stem="用户点「Remove」时，示例用哪一种方式停掉最早那个超时？",
         code="""
void TimerExample::on_button_delete_timer()
{
  int timer_number = m_timers.begin()->first;
  m_counters.erase(timer_number);
  m_timers[timer_number].disconnect();
  m_timers.erase(timer_number);
}""",
         right="对记下的 sigc::connection 调用 disconnect()",
         wrong=["指望下一次 on_timeout 返回 false，只靠槽返回值自动断开",
                "只删掉 m_counters 里的计数，超时回调就会自己停住",
                "调用 app->quit() 结束主循环，以此清掉进程里全部超时"],
         why="原文给出两种停法：connection.disconnect()，或在槽里返回 false。Remove 按钮走的是前者——先记住 connect() 返回的 connection，再手动 disconnect()。擦计数只是示例自己的状态清理；quit() 会关掉整个程序。",
         ref="Timeouts：sigc::connection::disconnect()；示例 on_button_delete_timer"),
    dict(id="tm24-io-1", page=IO, pos=2,
         stem="要把槽登记成「文件描述符有数据可读时再调」，第三个参数应写什么？",
         code="""
Glib::signal_io().connect(slot, fd, /* condition */ ____);""",
         right="Glib::IOCondition::IO_IN",
         wrong=["Glib::IOCondition::IO_OUT（描述符可写时才调用）",
                "Glib::IOCondition::IO_HUP（连接挂断时才调用）",
                "Glib::IOCondition::IO_ERR（描述符出错时才调用）"],
         why="原文列表：IO_IN 表示描述符上有数据可读时调用；IO_OUT 是可写，IO_HUP 是挂断，IO_ERR 是出错。官方 fifo 示例正是 connect(..., read_fd, Glib::IOCondition::IO_IN)。",
         ref="Monitoring I/O：IO_IN / IO_OUT / IO_PRI / IO_ERR / IO_HUP"),
    dict(id="tm24-io-2", page=IO, pos=3,
         stem="官方 fifo 示例用 lambda 包一层再 connect。相对 sigc::mem_fun()，lambda 少了什么？",
         code="""
Glib::signal_io().connect(
  [](Glib::IOCondition io_condition){ return MyCallback(io_condition); },
  read_fd, Glib::IOCondition::IO_IN);""",
         right="对象销毁时的自动断开：mem_fun 会在对象离开作用域时断掉",
         wrong=["返回 bool 的能力：lambda 根本不能当作 signal_io 的槽",
                "读取描述符的能力：lambda 里不允许再去调 IOChannel",
                "指定优先级的能力：只有 mem_fun 才能传入 priority"],
         why="原文：槽通常用 sigc::mem_fun() 或 sigc::ptr_fun() 建；若你不需要 mem_fun 在对象超出作用域时提供的自动断开，可以用 lambda。示例正是这种「不需要自动断开」的写法。",
         ref="Monitoring I/O：lambda 与 mem_fun 自动断开的取舍"),
    dict(id="tm24-id-1", page=ID, pos=1,
         stem="IdleExample 里两条连接各服务哪根进度条？负载升高时哪根会变慢？",
         code="""
Glib::signal_timeout().connect(
  sigc::mem_fun(*this, &IdleExample::on_timer), 50);
Glib::signal_idle().connect(
  sigc::mem_fun(*this, &IdleExample::on_idle));""",
         right="timeout 推上条、idle 推下条；加负载后变慢的是下条",
         wrong=["两条都走 timeout，只是间隔不同；负载高低都匀速前进",
                "idle 推上条、timeout 推下条；加负载后变慢的是上条",
                "idle 只在启动时跑一次，所以下面那根进度条几乎不动"],
         why="原文注释与后文：timeout 每 50ms 更新上条（C:），idle 尽可能快跑更新下条（D:）。需要周期性且速度不关键用 timeout；要尽可能多调用（后台算分形）用 idle。加负载后上条仍稳，下条变慢。",
         ref="Idle Functions：timeout 周期性；idle 尽可能多；示例负载实验"),
]

CHECKPOINT = [
    dict(id="tm24-cp-1", pos=2, locator="官方节页 sec-timeouts",
         stem="count_value=5、计数初值设为 count_value+1。on_timeout 第一次被调用时，终端大概打印什么？",
         code="""
bool TimerExample::on_timeout(int timer_number)
{
  std::cout << "This is timer " << timer_number;
  if (--m_counters[timer_number] == 0)
  {
    std::cout << " being disconnected" << std::endl;
    m_counters.erase(timer_number);
    m_timers.erase(timer_number);
    return false;
  }
  std::cout << " - " << m_counters[timer_number] << "/"
            << count_value << std::endl;
  return true;
}""",
         right="This is timer N - 5/5（尚未断开，返回 true）",
         wrong=["This is timer N being disconnected（第一次就返回 false）",
                "This is timer N - 0/5（已扣到 0，却仍返回 true 继续）",
                "什么都不打印：返回 true 之前主循环根本不会进回调"],
         why="添加超时时把计数设为 count_value+1（即 6）。第一次回调先 -- 得到 5，不等于 0，打印「- 5/5」并返回 true 继续。要连着倒数到 0 才打印 being disconnected 并返回 false；注释写明返回 false 时 Gtk::Main 会替你 disconnect。",
         ref="综合 Timeouts 示例：计数初值与返回 false 断开"),
    dict(id="tm24-cp-2", pos=0, locator="官方节页 sec-idle-functions 与 sec-timeouts",
         stem="要在界面空闲时尽量多跑计算，又要能随时停掉，该怎么连、怎么停？",
         right="signal_idle().connect(槽)；用 disconnect() 或让槽返回 false 停",
         wrong=["只能用 signal_timeout(1)，因为 idle 槽不能靠返回 bool 断开",
                "用 signal_io 监视 /dev/null，等所谓「空闲事件」再开始算",
                "把计算写进按钮 clicked 槽，主循环一空闲就会自动重入"],
         why="idle 的 connect 与 timeout 一样返回 connection，槽也是 bool()：disconnect() 或返回 false 都能删掉处理函数。timeout 适合周期性且速度不关键；clicked 只在点击时跑，不会在空闲时重入。",
         ref="综合 Idle Functions：connect / disconnect / 返回 false"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
