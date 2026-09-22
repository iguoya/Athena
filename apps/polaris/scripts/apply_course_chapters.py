#!/usr/bin/env python3
"""给每门课写入细分章节学习流程。指南针层：章名 + 一句干什么，不写教程。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLARIS = ROOT / "content" / "polaris.json"


def ch(chapter_id: str, title: str, summary: str, requires: list[str] | None = None) -> dict:
    return {
        "id": chapter_id,
        "title": title,
        "summary": summary,
        "requires": requires or [],
        "mastery": "usage",
    }


CHAPTERS: dict[str, list[dict]] = {
    "polaris.cs.c_lang": [
        ch("c.bytes", "字节、地址与变量", "先看见内存里有格子，变量是有类型的那一格。"),
        ch("c.pointer", "指针", "指针存的是地址；后续数组和结构体都靠它解释。", ["c.bytes"]),
        ch("c.array", "数组与指针算术", "连续格子怎么走；越界是从这里开始的。", ["c.pointer"]),
        ch("c.string", "字符串", "以零结尾的字节序列，不是抽象的“一句话”。", ["c.array"]),
        ch("c.struct", "结构体与对齐", "把相关字节捆成记录，并看清填充从哪来。", ["c.array"]),
        ch("c.heap", "动态分配与寿命", "谁分配、谁释放、指针何时失效。", ["c.pointer"]),
    ],
    "polaris.cs.cpp": [
        ch("cpp.object", "对象与构造", "对象什么时候开始存在、成员按什么顺序就位。"),
        ch("cpp.value", "值类别与移动", "左值 / 右值决定拷贝还是移交，实时路径要能说清。", ["cpp.object"]),
        ch("cpp.raii", "资源与 RAII", "用对象寿命管住内存、句柄和锁，不靠手工配对。", ["cpp.object"]),
        ch("cpp.template", "模板与泛型", "同一套结构如何在不同类型上实例化。", ["cpp.object"]),
        ch("cpp.stl", "标准库容器与算法", "会选容器、知道复杂度，而不是把 vector 当唯一工具。", ["cpp.template"]),
        ch("cpp.lifetime", "引用、临时量和悬空", "绑定活多久；这是后续并发和接口设计的暗礁。", ["cpp.value", "cpp.raii"]),
    ],
    "polaris.cs.python": [
        ch("py.script", "脚本与数据类型", "用它把试验步骤写成可重跑的脚本。"),
        ch("py.file", "文件、表格与批处理", "读日志、写对照表，地面数据处理的入口。", ["py.script"]),
        ch("py.plot", "绘图与对比", "同一组数画出能复核的图，而不是一次性截屏。", ["py.file"]),
        ch("py.pack", "环境与可复现", "依赖锁住，换机器还能跑出同一张表。", ["py.script"]),
    ],
    "polaris.cs.assembly": [
        ch("asm.reg", "寄存器与寻址", "CPU 看见的名字：寄存器、立即数、内存操作数。"),
        ch("asm.flag", "指令与标志位", "一条指令改了哪些状态，条件跳转看什么。", ["asm.reg"]),
        ch("asm.frame", "栈帧与调用约定", "参数、返回地址、被调用者保存寄存器怎么摆。", ["asm.reg"]),
        ch("asm.ir", "对照编译产物", "高级语言一行对应哪些指令，优化消掉了什么。", ["asm.frame"]),
        ch("asm.boot", "中断与启动代码", "向量表、现场保存，裸机从这里才能站起来。", ["asm.frame"]),
    ],
    "polaris.cs.computer_systems": [
        ch("sys.bits", "数的表示与对齐", "整数、字节序、对齐；总线数据从这里开始读得懂。"),
        ch("sys.gate", "门、加法器与 ALU", "“能算”在门级是怎么拼出来的。", ["sys.bits"]),
        ch("sys.isa", "指令与执行循环", "取指、译码、执行；程序如何变成一拍一拍的动作。", ["sys.gate"]),
        ch("sys.mem", "存储层次", "缓存 / 主存为什么让最坏延迟和均值不是一回事。", ["sys.isa"]),
        ch("sys.ex", "异常、中断与特权", "谁能打断当前指令，返回时现场还在不在。", ["sys.isa"]),
        ch("sys.abi", "调用约定与编译产物", "交叉编译的结果要能对上寄存器和栈。", ["sys.mem", "sys.ex"]),
    ],
    "polaris.cs.da": [
        ch("da.cost", "复杂度与最坏界", "先会量增长，再谈选结构。"),
        ch("da.linear", "数组、链表、栈与队列", "连续与链式、入队出队的代价。", ["da.cost"]),
        ch("da.tree", "树、堆与哈希", "有序、优先和均摊查找各自付出什么。", ["da.linear"]),
        ch("da.graph", "图的表示与遍历", "邻接怎么存，BFS / DFS 各回答什么。", ["da.linear"]),
        ch("da.sort", "排序与查找", "有序之后才能二分；不稳定排序会弄丢关联。", ["da.tree"]),
        ch("da.paradigm", "分治、贪心与动态规划", "同一问题为什么换一种切法。", ["da.cost", "da.graph"]),
    ],
    "polaris.cs.operating_systems": [
        ch("os.proc", "进程、线程与地址空间", "隔离从这里开始：谁看不见谁的内存。"),
        ch("os.sched", "调度与时间片", "谁先跑、能抢吗；实时里对应优先级和截止期。", ["os.proc"]),
        ch("os.mem", "内存与有界资源", "虚拟内存、页、上界；裁剪 RTOS 时要能指认。", ["os.proc"]),
        ch("os.sync", "同步与共享状态", "锁、信号量、死锁；并发课的操作系统面。", ["os.sched"]),
        ch("os.persist", "文件与持久化", "崩溃之后什么还在，什么必须重做。", ["os.mem"]),
        ch("os.isol", "保护、系统调用与分域", "用户态碰不到的东西；完整性检查挂在这里。", ["os.sync"]),
    ],
    "polaris.cs.concurrency": [
        ch("cc.share", "共享状态与竞态", "两个执行流碰同一块数据时，什么叫出错。"),
        ch("cc.lock", "锁、顺序与死锁", "互斥能换来什么，又会引入哪些等待。", ["cc.share"]),
        ch("cc.queue", "有界队列与交接", "控制周期里数据怎么交；队列深度就是延迟。", ["cc.lock"]),
        ch("cc.prio", "优先级反转与天花板", "低优先级占着资源时，截止期如何被拖死。", ["cc.lock"]),
        ch("cc.wait", "无锁、等待与唤醒", "什么时候不该自旋，中断里能做什么。", ["cc.queue"]),
    ],
    "polaris.cs.linux_sysprog": [
        ch("lx.proc", "进程、fork 与退出", "地面程序怎么起、怎么收，僵尸从哪来。"),
        ch("lx.fd", "文件描述符与 I/O", "一切皆 fd：文件、管道、套接字。", ["lx.proc"]),
        ch("lx.sig", "信号与终端", "异步通知会打断哪里，哪些在实时路径上不能用。", ["lx.proc"]),
        ch("lx.poll", "多路复用", "一个线程盯多个 fd，超时怎么设。", ["lx.fd"]),
        ch("lx.net", "套接字入门", "连上试验网和上位机的系统调用面。", ["lx.fd"]),
    ],
    "polaris.cs.computer_networks": [
        ch("net.layer", "分层与封装", "延迟出在哪一层，先靠分层说话。"),
        ch("net.link", "链路、帧与介质", "冲突、带宽和误码在最底下长什么样。", ["net.layer"]),
        ch("net.ip", "网络层与转发", "地址、路由、分片；丢包不一定是应用的错。", ["net.layer"]),
        ch("net.tp", "传输：可靠与实时", "重传、窗口、超时；测控更关心哪一种。", ["net.ip"]),
        ch("net.app", "应用层与数据链", "一条遥测/试验流如何落在端口和帧格式上。", ["net.tp"]),
        ch("net.sec", "完整性与不信任输入", "报文可以伪造；校验和认证挂在这一层。", ["net.app"]),
    ],
    "polaris.cs.network_programming": [
        ch("np.sock", "套接字与连接", "connect / listen 的状态机。"),
        ch("np.frame", "粘包、拆包与超时", "字节流不是消息；帧和超时必须自己定。", ["np.sock"]),
        ch("np.io", "多路 I/O 与长连接", "台上位机要扛住断线重连。", ["np.frame"]),
        ch("np.fail", "失败、重试与背压", "对端慢了怎么办，队列不能无限长。", ["np.io"]),
    ],
    "polaris.cs.engineering_practice": [
        ch("eng.repo", "版本与变更", "谁改了什么必须能指认。"),
        ch("eng.build", "构建与交叉编译", "同一份源码在主机和目标上都能复现。", ["eng.repo"]),
        ch("eng.test", "测试与持续集成", "每次提交有自动判据，不是靠手点。", ["eng.build"]),
        ch("eng.static", "静态分析与警告", "未定义行为和越界尽量在合入前抓住。", ["eng.build"]),
        ch("eng.trace", "需求、接口与追溯", "改动能回到需求；完整性检查写进验收。", ["eng.repo", "eng.test"]),
    ],
    "polaris.cs.dp": [
        ch("dp.why", "结构为什么要分层", "大型地面工具里，变化点要隔离。"),
        ch("dp.struct", "组合、适配与外观", "把已有接口收成稳定边界。", ["dp.why"]),
        ch("dp.behave", "策略、观察与状态", "行为可替换，但不在实时热路径上加虚表迷宫。", ["dp.why"]),
        ch("dp.bound", "实时系统里的边界", "哪些模式增加不可分析的间接，应该不用。", ["dp.struct", "dp.behave"]),
    ],
    "polaris.cs.practice": [
        ch("pr.spec", "需求与接口冻结", "先写清交什么、不交什么。"),
        ch("pr.split", "分系统切分", "谁负责采集、谁负责控制、谁负责记录。", ["pr.spec"]),
        ch("pr.integ", "联调与失败注入", "对端不在时系统表现是什么。", ["pr.split"]),
        ch("pr.repro", "可复现交付", "别人按文档能重跑，而不是只有你的机器能跑。", ["pr.integ"]),
        ch("pr.review", "评审与收口", "留下证据：测了什么、还剩什么风险。", ["pr.repro"]),
    ],
    "polaris.cs.model_dev": [
        ch("md.task", "任务与数据边界", "这个问题该不该用模型，数据从哪来。"),
        ch("md.eval", "可复现评测", "同一批样本、同一指标，别人能重跑。", ["md.task"]),
        ch("md.call", "受控调用与人工确认", "输出必须能被否决，不能闭环到执行器。", ["md.eval"]),
        ch("md.limit", "不进飞控", "延迟、不可解释和失败模式，决定它停在地面。", ["md.call"]),
    ],
    "polaris.ei.electronics_basics": [
        ch("ee.ohm", "电压、电流与欧姆", "电路的第一把尺子。"),
        ch("ee.kcl", "基尔霍夫与分压", "节点电流、回路电压，接地从这里认真起来。", ["ee.ohm"]),
        ch("ee.rc", "RC 暂态", "电容不是瞬时导通；时间常数决定边沿。", ["ee.kcl"]),
        ch("ee.inst", "表与示波器", "量程、探头、地；读数会骗人。", ["ee.ohm"]),
        ch("ee.filter", "一阶滤波与电源去耦", "进实验室就要会看纹波和带宽。", ["ee.rc", "ee.inst"]),
    ],
    "polaris.ei.analog": [
        ch("an.op", "运放与反馈", "理想模型先能算，再谈它何时失效。"),
        ch("an.bias", "偏置与小信号", "静态工作点不对，交流再漂亮也是假的。", ["an.op"]),
        ch("an.filter", "滤波器与带宽", "通带、截止、Q 值要能对上示波器。", ["an.bias"]),
        ch("an.noise", "噪声、失调与摆率", "非理想项如何把“算对了”变成板上偏。", ["an.op"]),
        ch("an.psu", "基准与线性电源", "传感前端的尺子本身要稳。", ["an.bias"]),
    ],
    "polaris.ei.digital": [
        ch("dg.comb", "组合逻辑", "门延迟和竞争冒险。"),
        ch("dg.seq", "时序、时钟与触发器", "建立 / 保持；没有时钟就没有数字系统。", ["dg.comb"]),
        ch("dg.fsm", "状态机", "把协议和控制器写成可验证的状态。", ["dg.seq"]),
        ch("dg.cdc", "跨时钟域", "直接采样是仿真过、上板翻车的典型原因。", ["dg.seq"]),
        ch("dg.time", "时序分析入门", "会读约束和违例，才配写 FPGA。", ["dg.fsm", "dg.cdc"]),
    ],
    "polaris.ei.mcu_8051": [
        ch("m51.sfr", "寄存器与存储映射", "外设就是特殊功能寄存器。"),
        ch("m51.irq", "中断", "谁打断主循环，现场怎么存。", ["m51.sfr"]),
        ch("m51.timer", "定时器与串口", "时基和最简单的字节通道。", ["m51.irq"]),
        ch("m51.doc", "查手册与时序图", "入门台阶的真正产出是这个习惯。", ["m51.sfr"]),
    ],
    "polaris.ei.stm32": [
        ch("mcu.clk", "时钟树与复位", "谁给谁供时钟，启动卡在哪。"),
        ch("mcu.gpio", "GPIO、EXTI 与功耗", "引脚仍是电路：上下拉、速度、回流。", ["mcu.clk"]),
        ch("mcu.dma", "DMA 与有界搬运", "CPU 不搬每个字节，延迟才可分析。", ["mcu.gpio"]),
        ch("mcu.timer", "定时器、PWM 与捕获", "控制周期和脉宽从这里长出来。", ["mcu.clk"]),
        ch("mcu.adc", "ADC 与采样触发", "和定时器、DMA 排成一条采集链。", ["mcu.dma", "mcu.timer"]),
        ch("mcu.link", "启动文件与链接脚本", "向量表、栈、段；交叉编译产物要对得上。", ["mcu.clk"]),
    ],
    "polaris.ei.sensors": [
        ch("se.phys", "物理量与误差源", "测的是什么，单位和不确定度。"),
        ch("se.front", "调理与增益", "运放网络如何把传感器接到 ADC。", ["se.phys"]),
        ch("se.anti", "抗混叠与采样", "采样定理在板上的那一层。", ["se.front"]),
        ch("se.cal", "标定与温漂", "数对了不等于量对了。", ["se.phys"]),
        ch("se.if", "数字接口与同步", "I2C / SPI / 脉冲，时间戳从哪来。", ["se.anti"]),
    ],
    "polaris.ei.protocols_bus": [
        ch("bus.lvl", "电平、极性与回流", "总线先是电路，再是协议。"),
        ch("bus.uart", "异步串行", "波特率、采样点和空闲。", ["bus.lvl"]),
        ch("bus.sync", "SPI 与 I2C", "时钟谁出、应答谁拉。", ["bus.lvl"]),
        ch("bus.can", "CAN 与仲裁", "多主机、优先级编码在位时间里。", ["bus.sync"]),
        ch("bus.la", "用逻辑分析仪对照手册", "波形对不上文字时，以波形为准。", ["bus.uart", "bus.can"]),
    ],
    "polaris.ei.pcb_design": [
        ch("pcb.sch", "原理图与网络", "先把连接说清楚，再谈布线。"),
        ch("pcb.lib", "封装与库", "焊盘和实物对不上，后面全废。", ["pcb.sch"]),
        ch("pcb.pwr", "电源分区与去耦", "数字、模拟、功率怎么隔。", ["pcb.sch"]),
        ch("pcb.route", "走线、回流与阻抗", "高速边沿开始不能当电阻。", ["pcb.pwr"]),
        ch("pcb.dfm", "可制造与可测", "打样、焊接、测试点。", ["pcb.lib", "pcb.route"]),
    ],
    "polaris.ei.freertos": [
        ch("rt.task", "任务与栈", "每个循环是一个任务，栈要有上界。"),
        ch("rt.prio", "优先级与抢占", "谁能打断谁，和截止期怎么对应。", ["rt.task"]),
        ch("rt.ipc", "队列、信号量与通知", "任务之间如何交数据。", ["rt.task"]),
        ch("rt.isr", "中断延迟与延迟处理", "ISR 里能做什么，必须推到任务。", ["rt.prio"]),
        ch("rt.wcet", "最坏抖动测量", "在真实调度器上测，不在纸上估。", ["rt.ipc", "rt.isr"]),
    ],
    "polaris.ei.fpga": [
        ch("fp.rtl", "RTL 与仿真", "先仿真出波形，再谈上板。"),
        ch("fp.seq", "时序电路落地", "状态机、使能、同步复位。", ["fp.rtl"]),
        ch("fp.sdc", "约束与时序收敛", "时钟、输入输出延迟。", ["fp.seq"]),
        ch("fp.cdc", "跨时钟与复位域", "FPGA 翻车最多的地方。", ["fp.sdc"]),
        ch("fp.io", "接口与流水", "采集通路如何焊成并行。", ["fp.seq"]),
    ],
    "polaris.ei.dsp": [
        ch("dsp.sample", "采样与量化", "位数、满量程、信噪比从这里来。"),
        ch("dsp.lti", "滤波与差分方程", "把信号与系统的式子写成可跑的循环。", ["dsp.sample"]),
        ch("dsp.fft", "频谱与窗", "泄漏、分辨率，和采样率怎么配。", ["dsp.lti"]),
        ch("dsp.fix", "定点与溢出", "实时链路上浮点往往不是选项。", ["dsp.lti"]),
        ch("dsp.budget", "耗时预算", "一帧算不完，再好的算法也没用。", ["dsp.fft", "dsp.fix"]),
    ],
    "polaris.ei.signals_systems": [
        ch("ss.sig", "连续与离散信号", "同一段物理过程的两种写法。"),
        ch("ss.lti", "线性时不变与卷积", "系统对输入做什么，卷积是定义不是技巧。", ["ss.sig"]),
        ch("ss.ft", "傅里叶与频谱", "时域看不清的，频域往往一眼能看。", ["ss.lti"]),
        ch("ss.sample", "采样定理与混叠", "DSP、通信、控制共用这把尺子。", ["ss.ft"]),
        ch("ss.stab", "稳定性与频率响应", "闭环会不会抖，先在这里判断。", ["ss.lti"]),
    ],
    "polaris.ei.matlab": [
        ch("ml.mat", "矩阵、脚本与绘图", "把一次计算收成可重跑的文件。"),
        ch("ml.time", "时间序列与信号处理", "和采集链对上同一套时标。", ["ml.mat"]),
        ch("ml.sl", "Simulink 连续 / 离散", "对象、延迟、控制器放在同一时间轴。", ["ml.time"]),
        ch("ml.step", "固定步长与代数环", "能仿真不等于能上实时机。", ["ml.sl"]),
        ch("ml.export", "对照数据与代码生成边界", "导出别人能重跑的时间序列。", ["ml.step"]),
    ],
    "polaris.ei.communications": [
        ch("cm.mod", "调制与星座", "符号如何变成波形。"),
        ch("cm.ch", "信道、噪声与误码", "弱场时链路会怎样坏。", ["cm.mod"]),
        ch("cm.sync", "帧、时钟与同步", "失锁是帧、时钟还是信道。", ["cm.ch"]),
        ch("cm.link", "链路预算", "增益、损耗、余量要能算。", ["cm.ch"]),
        ch("cm.ttc", "遥测遥控数据链", "天地 / 台架上这条链怎么验收。", ["cm.sync", "cm.link"]),
    ],
    "polaris.ei.control": [
        ch("ct.loop", "测—比—执行", "开环和闭环差在有没有用误差去改动作。"),
        ch("ct.model", "对象、延迟与扰动", "先会写一阶加延迟，再谈整定。", ["ct.loop"]),
        ch("ct.pid", "PID 与基本整定", "三个数各管什么，乱拧为什么会散。", ["ct.model"]),
        ch("ct.stab", "稳定裕度", " Bode / 根轨迹不必一次讲完，但要能判断会不会抖。", ["ct.model"]),
        ch("ct.test", "阶跃与抗扰实验", "超调、调节时间可重复，才算整定完成。", ["ct.pid", "ct.stab"]),
    ],
    "polaris.ei.electromagnetics": [
        ch("em.field", "场与路的边界", "集总电路何时失效。"),
        ch("em.line", "传输线与特征阻抗", "走线是有延迟和反射的。", ["em.field"]),
        ch("em.refl", "反射、端接与串扰", "失配台阶从哪来。", ["em.line"]),
        ch("em.emc", "回流、接地与辐射来源", "给 EMC 规则一个物理理由。", ["em.field", "em.refl"]),
    ],
    "polaris.ei.linux_driver": [
        ch("drv.char", "字符设备与文件接口", "用户态看见的那一侧。"),
        ch("drv.irq", "中断与下半部", "硬中断里不能睡觉。", ["drv.char"]),
        ch("drv.dt", "设备树与绑定", "板级差异写在数据里，不写死在驱动。", ["drv.char"]),
        ch("drv.dma", "缓冲与 DMA", "内核到硬件的搬运契约。", ["drv.irq"]),
    ],
    "polaris.ei.motor_control": [
        ch("mo.pwm", "PWM 与功率级", "电压怎么变成转矩的入口。"),
        ch("mo.i", "电流环", "最快的那一环，采样必须跟上。", ["mo.pwm"]),
        ch("mo.p", "速度 / 位置环", "外环建立在电流环稳住之后。", ["mo.i"]),
        ch("mo.sense", "编码器与电流传感", "反馈坏了，环只会抖。", ["mo.i"]),
        ch("mo.prot", "过流与失步保护", "机电系统先保证不毁。", ["mo.p", "mo.sense"]),
    ],
    "polaris.ei.embedded_linux": [
        ch("el.boot", "启动与根文件系统", "从复位到能跑用户态。"),
        ch("el.dt", "设备树与板级", "外设如何被内核认到。", ["el.boot"]),
        ch("el.user", "用户态服务与网络", "地面台架和网关的常见形态。", ["el.boot"]),
        ch("el.rt", "实时限制", "为什么弹上闭环通常不走这里。", ["el.user"]),
    ],
    "polaris.ei.edge_ai": [
        ch("ai.quant", "量化与算子", "模型如何缩小到端侧。"),
        ch("ai.mem", "内存与延迟预算", "跑得动不等于跑得完。", ["ai.quant"]),
        ch("ai.deploy", "地面部署", "监测和试验可以放，飞控不放。", ["ai.mem"]),
        ch("ai.guard", "失败与人工确认", "推理失败时系统还剩什么。", ["ai.deploy"]),
    ],
}

# ACM / IEEE-CS CS2013 知识单元掌握度：Familiarity / Usage / Assessment。
# 熟悉 = 能指认；运用 = 能动手做；评估 = 能比较方案、判断边界。
ASSESSMENT = {
    "c.pointer", "cpp.raii", "cpp.value", "sys.mem", "da.cost", "os.sched",
    "cc.queue", "net.tp", "eng.build", "mcu.dma", "bus.la", "rt.wcet",
    "fp.cdc", "dsp.budget", "ss.sample", "ct.test", "se.anti", "ee.inst",
    "dg.seq", "rt.prio",
}
FAMILIARITY = {
    "md.limit", "el.rt", "net.sec", "dp.why", "ai.guard", "sys.gate",
    "cm.mod", "em.field", "asm.boot", "sys.ex", "sys.abi", "da.paradigm",
    "os.isol", "os.persist", "cc.prio", "cc.wait", "lx.sig", "np.fail",
    "eng.static", "dp.bound", "pr.review", "an.noise", "dg.cdc", "dg.time",
    "mcu.link", "se.cal", "bus.can", "pcb.route", "fp.sdc", "dsp.fix",
    "ss.stab", "ml.step", "ml.export", "cm.link", "ct.stab", "em.emc",
    "drv.dma", "mo.prot", "py.pack", "cpp.template", "net.link", "dp.behave",
    "an.psu", "m51.timer", "fp.io", "el.user", "ai.quant",
}


def decorate(chapters: list[dict]) -> list[dict]:
    for chapter in chapters:
        chapter_id = chapter["id"]
        if chapter_id in ASSESSMENT:
            chapter["mastery"] = "assessment"
        elif chapter_id in FAMILIARITY:
            chapter["mastery"] = "familiarity"
        else:
            chapter["mastery"] = "usage"
        # 运用、评估是重要知识点，走实践；熟悉走理论。实践要能直接感到这门课为什么必要。
        chapter["kind"] = "practice" if chapter["mastery"] != "familiarity" else "theory"
        chapter["hands_on"] = chapter["kind"] == "practice"
        chapter.pop("necessity", None)
        chapter.pop("band", None)
    return chapters


def main() -> None:
    polaris = json.loads(POLARIS.read_text(encoding="utf-8"))
    missing: list[str] = []
    for entry in polaris["maps"]:
        if entry.get("graph_kind") != "course":
            continue
        for node in entry.get("nodes", []):
            node_id = node["id"]
            chapters = CHAPTERS.get(node_id)
            if not chapters:
                missing.append(node_id)
                continue
            node["chapters"] = decorate(chapters)
    if missing:
        raise SystemExit("这些课程还没有学习流程：" + ", ".join(missing))
    POLARIS.write_text(json.dumps(polaris, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote chapters for", sum(1 for v in CHAPTERS.values() if v), "courses")


if __name__ == "__main__":
    main()
