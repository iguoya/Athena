#include "registry/domain_graph.h"

#include "registry/progress_stats.h"

#include <algorithm>
#include <set>
#include <string>
#include <utility>

namespace {

struct Prereq {
    const char* id;
    const char* reason;      // 关联的历史 / 概念来路，以及学它对后者的必要性
    bool strong = true;      // false = 虚线"来路"，说明渊源但不是入学门槛
};

// 归入电子信息方向图的节点；其余都在计算机方向图。
const set<string>& electronics_ids() {
    static const set<string> ids = {
        "electronics_basics", "mcu_8051", "fpga", "sensors", "stm32",
        "protocols_bus", "dsp", "motor_control", "pcb_design", "freertos",
        "embedded_linux", "edge_ai", "linux_driver"};
    return ids;
}

// 推荐入门起点：从这些里任选一个开始都合理。
const set<string>& entry_ids() {
    static const set<string> ids = {
        "cpp", "c_lang", "python", "electronics_basics",
        "engineering_practice"};
    return ids;
}

// 首页学科路线图。声明顺序 = 层内从左到右的排布顺序。prerequisites 用
// 本表内的 id 互相引用，必须无环（build 时按层号推导，成环的节点会退到
// 第 0 层，不会崩）。
//
// 方向：软硬结合、只收“能验证”的实践科目——每个节点标注验证方式
// （编程 / 开发板 / 硬件仪表）和优先级。content 写“讲什么”，purpose 写
// “作用 / 为什么学”，difficulty 写“难点”，三者分开。纯理论科目一律不建
// 节点，见 theory_topics()。
struct DomainSpec {
    const char* id;
    const char* title;
    const char* content;
    const char* purpose;
    const char* difficulty;
    const char* icon;
    DomainKind kind;
    VerifyMode verify;
    DomainPriority priority;
    DomainTrack track;
    const char* note;
    vector<Prereq> prerequisites;
    // 这个领域由 apps/ 下的独立应用承载时填它的 id，其余节点留空。
    const char* app_id = nullptr;
};

const vector<DomainSpec>& domain_specs() {
    static const vector<DomainSpec> specs = {
        // —— L0：互不依赖的独立起点。它们各自是一条学习线的源头，
        //         没有谁必须先学谁。——
        {"assembly", "汇编语言",
         "某种指令集（x86-64 或 ARM）的寄存器与寻址方式、指令与标志位、"
         "调用约定与栈帧、中断响应，以及对照高级语言看编译产物。",
         "这是所有软件的历史原点：早期程序直接用机器码和汇编写成，"
         "今天你仍然靠它看懂反汇编、定位崩溃、理解性能和安全问题的"
         "最底层原因，也靠它给裸机写启动代码。它给你一把尺子——之后"
         "每一层抽象“省掉了什么、又要付出什么”，都能拿它来量。",
         "细节琐碎、可读性差；调用约定、栈帧布局和寄存器分配容易绕晕。",
         "application-x-executable-symbolic", DomainKind::Planned,
         VerifyMode::Code, DomainPriority::Core, DomainTrack::Systems, "",
         {}},
        {"computer_systems", "计算机系统基础",
         "从布尔代数、逻辑门到加法器和 ALU，指令集与体系结构，"
         "数的表示、字节序与对齐，寄存器 / 高速缓存 / 主存的存储层次，"
         "以及“一段程序在机器上到底怎么被执行”。",
         "它回答的是“计算机凭什么能算”这个最根本的问题，是操作系统、"
         "汇编、嵌入式共同的地基。历史上体系结构与操作系统一直相互"
         "推动：分时需求催生了保护模式，多核催生了新的缓存一致性和"
         "调度模型。不打这个底，上层很多设计都会变成“背下来但说不清"
         "为什么”的黑盒。",
         "抽象层多，从概念到实物的对应需要反复搭建。",
         "computer-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Core, DomainTrack::Systems, "逻辑门 / CPU 模拟器",
         {}},
        {"electronics_basics", "电路基础",
         "数字电路（门、触发器、时序逻辑、译码）与模拟电路（分压、"
         "RC、运放、三极管开关），面包板搭建，万用表和示波器的使用。",
         "所有硬件方向的地基：单片机的每一个引脚都是一段真实电路，"
         "点灯要算限流电阻、接按键要处理上下拉和抖动、接传感器要判断"
         "电平和是否需要分压。它也是独立的一门——不依赖任何编程知识，"
         "但没有它，后面的单片机和 PCB 只能照着接线图抄，一换器件就卡住。",
         "模拟部分直觉难建立；仪器使用和排错要靠动手积累。",
         "applications-science-symbolic", DomainKind::Planned,
         VerifyMode::Bench, DomainPriority::Core, DomainTrack::Hardware,
         "面包板 / 万用表 / 示波器", {}},
        {"da", "数据结构与算法",
         "线性表 / 树 / 图 / 哈希表的手写实现，排序与查找，"
         "分治 / 贪心 / 动态规划 / 回溯，以及复杂度分析。",
         "算法思想本身与语言无关，但落到“写出边界正确、复杂度可控"
         "的代码”这一步就离不开一门趁手的语言。它的价值是把“想到"
         "一个解法”变成能跑、能测的实现——几乎每个真实项目的核心"
         "逻辑都是某种数据结构加某种算法。",
         "从思路到代码的边界处理；复杂度分析和状态设计（尤其动态规划）。",
         "applications-science-symbolic", DomainKind::Available,
         VerifyMode::Code, DomainPriority::Core, DomainTrack::Engineering, "",
         {{"cpp",
           "本平台的数据结构课是用 C++ 手写实现每一种结构的：链表和"
           "树要用指针和明确的所有权，容器要用模板和 RAII，迭代器要"
           "重载运算符，性能对比要贴着内存布局看。算法思想虽然语言"
           "无关，但要读写这些实现、对照标准库的 vector / map / "
           "priority_queue，得先掌握 C++ 的类、模板和内存管理。"}}},
        {"engineering_practice", "工程实践与工具链",
         "构建系统与交叉编译，Git 与协作流程，单元测试与 TDD，"
         "调试器、Sanitizer 与静态分析，持续集成，发布与打包。",
         "这是一套与语言、领域都无关的元技能：它决定你能不能可靠地"
         "做出、改动、交付一个项目。任何一条学习线做到“写真实代码”"
         "的程度，都会立刻受益，所以越早养成越省事。",
         "工具零散、配置繁琐；难点在于坚持用，而不是知道有。",
         "applications-utilities-symbolic", DomainKind::Planned,
         VerifyMode::Code, DomainPriority::Core, DomainTrack::Engineering, "",
         {}},
        {"python", "Python 语言",
         "语法与数据模型、标准库与第三方包生态、脚本与自动化、"
         "虚拟环境与依赖管理、与 C/C++ 的绑定和扩展。",
         "一门自成体系的语言，1991 年问世，定位是“可读、够用、"
         "生态丰富”。它是数据处理、快速原型、自动化和人工智能的"
         "默认工具。它和 C 系语言是互补关系而不是先后关系——一个"
         "偏开发效率，一个偏运行效率，不需要先学别的语言才能学它。",
         "动态类型下大工程容易失控；性能和并发（GIL）需要权衡。",
         "text-x-generic-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Recommended, DomainTrack::Language, "", {}},

        // —— L1：从某个 L0 起点直接长出的第一层。——
        {"c_lang", "C 语言编程",
         "指针与内存布局、数组与字符串、结构体与联合、预处理器、"
         "分离编译与链接、完全手动的资源管理。",
         "1972 年 Dennis Ritchie 为重写 Unix 而设计 C，把它定位成"
         "“可移植的汇编”：保留对内存和硬件的直接控制，同时摆脱对"
         "具体指令集的依赖。此后半个世纪，操作系统内核、单片机固件、"
         "各种语言的运行时几乎都用 C 写成。它是软硬结合方向真正的"
         "枢纽语言。",
         "指针和手动内存管理陷阱多，未定义行为编译器不拦你。",
         "text-x-csrc-symbolic", DomainKind::ExternalApp, VerifyMode::Code,
         DomainPriority::Core, DomainTrack::Language, "",
         {{"assembly",
           "历史与概念上 C 都是从汇编演进而来的“可移植汇编”。它保留了"
           "对内存和硬件的直接控制，只是换上一层不绑定指令集的语法。"
           "C 里那些最容易踩坑的设计——指针运算、数组退化为指针、"
           "调用栈布局、`volatile`、未定义行为——单看 C 标准像一堆"
           "任意规定，落到汇编层面（寄存器、栈帧、寻址方式、编译器"
           "到底生成了什么）才真正讲得通。这属于“知道渊源会更透彻”，"
           "不是入学门槛——完全可以先上手 C，回头再补汇编。",
           false}},
         "c"},
        {"operating_systems", "操作系统",
         "手写内存分配器、用户态协作式 / 抢占式调度器、"
         "极简内存文件系统、页面替换与缓存算法。",
         "操作系统是对硬件的抽象与复用——把一台机器变成很多个看起来"
         "独占的执行环境。它是 Linux 驱动、嵌入式 RTOS 这些方向的"
         "概念来源：进程、上下文切换、虚拟内存、并发原语最早都是在"
         "这里定义清楚的。",
         "并发叠加底层，环境搭建成本高；正确性难以验证。",
         "preferences-system-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Recommended, DomainTrack::Systems, "内核模拟器 / QEMU",
         {{"computer_systems",
           "操作系统的每一项机制都是在管理某种硬件资源：进程调度对应"
           "CPU 与上下文，虚拟内存对应 MMU 和多级页表，文件缓存与"
           "并发对应存储层次和缓存一致性。历史上二者一直共同演进——"
           "分时系统催生了 CPU 的保护模式，多核催生了新的调度与内存"
           "一致性模型。跳过体系结构直接学 OS，大量机制会变成“知道"
           "这么做但答不上为什么”的黑盒。"}}},
        {"model_dev", "模型开发",
         "神经网络与反向传播，训练 / 验证 / 推理的完整流程，"
         "主流框架，数据管道与评估指标，模型导出与部署。",
         "让机器从数据里学规律，做预测、分类、生成这类难以用规则"
         "写死的任务。核心是理解“数据、算力、模型结构”三者如何"
         "共同决定最终效果。",
         "训练不稳定、调参经验性强；数据质量往往才是真正的上限。",
         "applications-science-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Optional, DomainTrack::AI, "Python 环境 / GPU 可选",
         {{"python",
           "从 2015 年前后开始，深度学习的框架（TensorFlow、PyTorch）、"
           "数据处理库（NumPy、pandas）、可视化和实验管理工具几乎"
           "全部以 Python 为接口层。模型开发的日常工作——搭数据管道、"
           "写训练循环、画损失曲线、做超参搜索——本身就是写 Python "
           "代码。先能熟练用 Python 处理数据和组织程序，才谈得上"
           "读框架文档、复现论文。而线性代数与概率作为数学基础，"
           "见右下“理论科目”，配合教材了解即可。"}}},

        // —— L2：语言线与嵌入线的主干在这里汇合。——
        {"cpp", "C++ 程序设计",
         "类型系统与值类别，资源管理与 RAII，面向对象，模板与泛型"
         "编程，标准库容器与算法，并发基础。",
         "1979 年 Bjarne Stroustrup 在贝尔实验室做“C with Classes”，"
         "1983 年定名 C++，至今仍以“兼容 C、零开销抽象”为纲领。"
         "它把 C 的底层控制力和高级抽象结合起来，是需要又快又能建"
         "大型结构的场合（游戏引擎、数据库、桌面软件、这个平台本身）"
         "的主力语言。",
         "语义细节多：值类别、对象生命周期、模板报错、从 C 继承来的"
         "未定义行为。",
         "applications-development-symbolic", DomainKind::Available,
         VerifyMode::Code, DomainPriority::Core, DomainTrack::Language, "",
         {{"c_lang",
           "C++ 起初就是在 C 上做加法——“C with Classes”这个名字说明"
           "了一切，至今仍与 C 高度兼容。C++ 的对象模型、构造与析构、"
           "RAII、模板实例化全部建立在 C 的内存布局和编译链接模型"
           "之上，报错信息和未定义行为也多半是 C 语义的延伸。理解 C "
           "的指针和手动内存管理之后，RAII、移动语义这些设计的动机"
           "会清楚很多。但这是来路，不是门槛：C++ 也可以作为第一门"
           "语言直接上手，两者并行学也行。",
           false}}},
        {"linux_sysprog", "Linux 系统编程",
         "进程与线程、fork/exec，管道与共享内存等 IPC，文件与 I/O，"
         "信号，套接字，以及系统调用的错误处理。",
         "写出真正跑在操作系统之上、直接使用内核服务的程序。它是"
         "并发、网络、驱动这几条线的共同基础，也是亲手体会“用户态"
         "与内核态边界”的地方。",
         "错误处理和资源清理繁琐，并发场景下更甚；调试要靠 strace "
         "这类工具。",
         "utilities-terminal-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Core, DomainTrack::Systems, "Linux 环境 / 虚拟机",
         {{"c_lang",
           "Unix 及其后代 Linux 的系统调用接口从第一天起就是用 C "
           "描述的：`open`/`read`/`fork`/`mmap` 的函数原型、`errno` "
           "约定、以指针传入传出的 `struct` 参数，全是 C 的方式。"
           "系统编程要成天和裸缓冲区、位标志、信号处理函数、"
           "谁负责释放资源打交道，这些正是 C 最擅长、也最容易出错"
           "的地方。有了 C 的手感，才能照着 man page 直接上手。"}}},
        {"mcu_8051", "51 单片机",
         "最小系统与时钟，GPIO，定时器 / 计数器，中断系统，"
         "串口（UART），用 C51 直接读写特殊功能寄存器。",
         "嵌入式的入门台阶：第一次让代码变成看得见的物理动作，"
         "并建立“查数据手册、看时序图、按位配置寄存器”的习惯。"
         "8051 内核 1980 年由 Intel 推出，资源少、外设简单，正因为"
         "简单，特别适合把嵌入式的基本套路一次看清楚。",
         "从纯软件转到要关心时序、电平、上下拉；工具链和烧录环境"
         "也要折腾。",
         "media-flash-symbolic", DomainKind::Planned, VerifyMode::Board,
         DomainPriority::Core, DomainTrack::Hardware, "开发板 / Proteus 仿真",
         {{"electronics_basics",
           "单片机的每个引脚都连着一段真实电路。点亮一个 LED 要算"
           "限流电阻，接按键要处理上下拉和机械抖动，接传感器要确认"
           "电平匹配、要不要分压或电平转换。程序写对了但现象不对时，"
           "示波器和万用表是唯一的排查手段。不懂电路，单片机就只能"
           "照抄接线图。"},
          {"c_lang",
           "从 8051 到今天，单片机固件的主力语言一直是 C：直接对"
           "寄存器地址赋值，用位运算配置外设，手动管理只有几十到"
           "几百字节的 RAM。这里没有操作系统兜底，C 的每一个未定义"
           "行为都可能表现成莫名其妙的硬件现象，所以要先把 C 的"
           "指针和内存管理练扎实。"},
          {"assembly",
           "裸机开发绕不开汇编：启动文件要手工设置堆栈指针和中断"
           "向量表，进入 main 之前的初始化、精确到指令周期的延时、"
           "读反汇编定位死机，都得能看懂汇编。8051 的中断响应和 SFR "
           "操作尤其贴近指令层。这是加分项而非前置——先用 C 玩起来，"
           "遇到时序和启动代码再回头补汇编也可以。",
           false}}},
        {"fpga", "FPGA 与硬件描述语言",
         "Verilog / VHDL，组合逻辑与时序逻辑，有限状态机，"
         "阻塞 / 非阻塞赋值，仿真（testbench）、综合、布局布线与"
         "时序约束，上板验证。",
         "和单片机是数字硬件的两条并行路线：单片机是一颗 CPU 顺序"
         "执行指令，FPGA 是把逻辑直接“焊”成并行电路，没有取指周期。"
         "用来做高速采集、并行信号处理、自定义接口、硬件加速，以及"
         "在一片芯片上搭出一个完整数字系统。数字电路学的门和触发器，"
         "在这里第一次变成可以随手改写的东西。",
         "思维方式要从“顺序执行”切换到“所有逻辑同时发生”；时序收敛"
         "和跨时钟域是长期难点。",
         "application-x-firmware-symbolic", DomainKind::Planned,
         VerifyMode::Board, DomainPriority::Recommended, DomainTrack::Hardware,
         "FPGA 开发板 + 仿真器",
         {{"electronics_basics",
           "FPGA 就是把数字电路里的门、触发器、译码器、计数器做成"
           "可编程的：写 HDL 本质上是在描述一张逻辑电路图，综合工具"
           "再把它映射到芯片里的查找表和寄存器上。不先理解组合逻辑、"
           "时序逻辑、建立 / 保持时间、竞争冒险，写出来的代码仿真"
           "能过、上板就出问题。"}}},
        {"sensors", "传感器与信号调理",
         "常见传感器（温度、光、加速度、电流、应变等）的原理与接口，"
         "放大与偏置、抗混叠滤波、基准与 ADC，噪声来源与抑制，"
         "标定与线性化。",
         "把真实世界的物理量变成单片机能读、读得准的数字。几乎每个"
         "嵌入式项目的第一步都是“先把信号采干净”——采集链路没做好，"
         "后面再多算法也是放大噪声。",
         "模拟前端对噪声、接地、布线敏感；标定要耐心，要有参照标准。",
         "utilities-system-monitor-symbolic", DomainKind::Planned,
         VerifyMode::Bench, DomainPriority::Recommended, DomainTrack::Hardware,
         "传感器 + 万用表 / 示波器",
         {{"electronics_basics",
           "信号调理就是模拟电路的直接应用：用运放搭同相 / 差分"
           "放大，用 RC 或有源滤波器做抗混叠，靠分压和基准把信号"
           "落进 ADC 量程。运放、滤波、阻抗这些概念不清楚，采回来"
           "的数据就是一堆噪声。"}}},

        // —— L3：各条线上第一层真正的“专业方向”。——
        {"dp", "设计模式",
         "创建型 / 结构型 / 行为型三类经典模式的动机、结构、"
         "协作方式和适用边界，以及它们试图化解的耦合问题。",
         "帮你识别“这段代码为什么难改”，并用经过检验的结构重新"
         "组织依赖关系；读框架和大型代码库时，也能一眼认出作者"
         "在用哪种套路。",
         "容易套用过度——为了用模式而增加间接层，反而更难懂。",
         "applications-system-symbolic", DomainKind::Available,
         VerifyMode::Code, DomainPriority::Recommended, DomainTrack::Engineering,
         "",
         {{"cpp",
           "1994 年《设计模式》成书时，示例代码用的是 C++ 和 "
           "Smalltalk；GoF 的 23 个模式本质上是“如何用面向对象特性"
           "化解耦合”的经验总结。策略、装饰器、观察者、访问者这些"
           "都直接依赖虚函数、继承、组合和接口这几样东西。没有一门"
           "具备完整面向对象能力的语言垫底，模式就退化成背结构图。"}}},
        {"concurrency", "并发与并行",
         "锁与条件变量、无锁数据结构、线程池、异步与协程、内存序，"
         "并用 ThreadSanitizer 复现数据竞争。",
         "写出正确的多线程代码，并理解高并发服务和 RTOS 任务同步"
         "背后共同的难点：多个执行流共享状态时如何不出错。",
         "非确定性的 bug 难复现、难调试；内存序是深水区。",
         "system-run-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Recommended, DomainTrack::Systems, "",
         {{"linux_sysprog",
           "实用并发的原语——线程、互斥量、条件变量、原子操作、"
           "内存屏障——都是操作系统和硬件提供、经由系统编程接口"
           "（pthread、futex 等）暴露出来的。数据竞争、死锁、惊群"
           "这些问题也只有在真正被内核调度的线程上才复现得出来。"
           "先能在系统层面创建线程、管理它们的生命周期，再谈并发"
           "模型和无锁结构才不悬空。"}}},
        {"computer_networks", "计算机网络",
         "OSI / TCP-IP 分层，以太网与交换，IP 与路由、子网与 NAT，"
         "TCP 的连接管理与拥塞控制、UDP，DNS / DHCP / HTTP / TLS，"
         "用 Wireshark 抓包对照 RFC，动手实现 ARP / IP / TCP 的"
         "最小子集和常见客户端 / 服务端。",
         "网络是现代软件的默认运行环境。理解每一层的职责，你才能"
         "判断一次延迟或丢包出在应用、传输还是链路，才能设计和排查"
         "分布式系统的通信。它实践性很强：抓包分析、手写精简协议栈、"
         "配路由和防火墙、用 tc / netem 模拟弱网，每一项都能上手"
         "验证——它不是只能背的理论课。",
         "协议细节多、状态机复杂（尤其 TCP）；抓包时要能把二进制"
         "字节和协议字段一一对上。",
         "network-workgroup-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Core, DomainTrack::Systems, "",
         {{"linux_sysprog",
           "抓包、构造原始数据包、实现协议栈都要在系统层面收发字节："
           "raw socket / AF_PACKET、libpcap、和内核的网络缓冲区打交道，"
           "都是系统编程接口。先能管好文件描述符和缓冲区，才搭得起"
           "自己的协议栈或抓包工具。"}}},
        {"network_programming", "网络编程",
         "TCP/UDP 套接字，自己实现基于行或二进制的应用层协议，"
         "I/O 多路复用（epoll/kqueue），超时与断线重连。",
         "做联网程序、服务端、设备之间的通信；把网络协议落成能跑、"
         "能抓包对照的代码。",
         "边界情况多：粘包、半连接、部分写、大量并发连接的管理。",
         "network-wired-symbolic", DomainKind::Planned, VerifyMode::Code,
         DomainPriority::Recommended, DomainTrack::Systems, "",
         {{"computer_networks",
           "写套接字程序前要先懂 TCP 和 UDP 的区别、端口和地址、"
           "连接的建立与关闭在网络上到底发生了什么。理解了协议的"
           "实际行为，粘包、Nagle 算法、TIME_WAIT 这些编程时绕不开"
           "的现象才不是玄学。"},
          {"linux_sysprog",
           "套接字 API 本身就是一组系统调用，和文件描述符、"
           "`select`/`poll`/`epoll` 事件模型、非阻塞 I/O 深度绑定。"
           "网络程序的难点——粘包与拆包、半关闭、部分写、超时重连、"
           "并发连接管理——都是系统编程问题的延伸。"}}},
        {"linux_driver", "Linux 驱动开发",
         "字符设备与文件操作接口，内核模块的加载与卸载，"
         "中断处理与并发原语，内核内存管理与 DMA，设备树。",
         "打通“用户态程序”和“具体硬件”这两端，是做嵌入式 Linux "
         "产品、给单板计算机适配外设的核心能力。",
         "内核态没有内存保护，一个空指针就是整机崩溃；调试手段"
         "有限，要靠交叉编译和串口日志。",
         "drive-harddisk-symbolic", DomainKind::Planned, VerifyMode::Board,
         DomainPriority::Optional, DomainTrack::Systems, "SBC / 虚拟机",
         {{"embedded_linux",
           "写驱动之前要先有一个跑起来的嵌入式 Linux 系统：知道"
           "内核怎么编译、设备树怎么描述硬件、根文件系统里放什么，"
           "模块才有地方加载、有 log 可看。"},
          {"linux_sysprog",
           "写驱动之前还要站在“用户程序怎么使用这个设备”的角度："
           "设备文件、`ioctl`、`mmap`、阻塞与非阻塞语义，都是系统"
           "编程里已经见过的接口，驱动实现的正是这些接口在内核的"
           "另一侧。熟悉用户态的调用约定，才知道自己在实现什么契约。"},
          {"operating_systems",
           "驱动是内核的一部分，运行在没有内存保护、可以直接触碰"
           "硬件的环境里。中断上下文、内核态并发与加锁、内存分配"
           "与 DMA、设备树——每一样都要求先理解内核的进程模型、"
           "并发模型和内存模型。"}}},
        {"stm32", "STM32",
         "ARM Cortex-M 内核与异常模型，时钟树，GPIO / 定时器 / "
         "DMA / ADC 等外设，寄存器操作与 HAL 库的取舍，SWD 调试。",
         "当前最主流的 32 位单片机，用来做电机控制、数据采集、"
         "带无线或有线通信的产品级固件。是嵌入式从“会点灯”走向"
         "“做产品”的分水岭。",
         "外设多、时钟树配置繁杂；要在 HAL 的便利和寄存器的可控"
         "之间不断权衡。",
         "application-x-firmware-symbolic", DomainKind::Planned,
         VerifyMode::Board, DomainPriority::Core, DomainTrack::Hardware,
         "开发板 + 调试器",
         {{"mcu_8051",
           "先在 8051 这种资源少、外设简单的芯片上，把“一个外设 = "
           "一组寄存器 + 一个中断”的心智模型和查手册、看时序图的"
           "习惯建立起来。STM32 是同一套思路的放大版：外设更多、"
           "时钟树更复杂、还多了 DMA 和总线矩阵，但底层套路一致。"
           "跳过入门芯片直接上 STM32，很容易被 HAL 和几百页参考"
           "手册淹没，只会照抄例程。"}}},
        {"practice", "应用实践",
         "把语言、数据结构和算法用在一个自成一体的小项目上"
         "（如二阶魔方求解器），完整走一遍需求拆解、实现、测试和迭代。",
         "检验前面学到的东西能不能拼起来解决一个真问题；建议在每"
         "学完一段之后都回来做一个。",
         "难在收口：控制范围、把一个玩具做到“确实能用”。",
         "applications-games-symbolic", DomainKind::Available, VerifyMode::Code,
         DomainPriority::Recommended, DomainTrack::Capstone, "",
         {{"cpp",
           "平台当前的实践项目——二阶魔方求解器——是用 C++ 写的："
           "状态编码、搜索、剪枝都用到了类、标准库容器和模板。"
           "要读懂并扩展它，先要有 C++ 的基础。"},
          {"da",
           "魔方求解的核心是状态空间搜索：BFS 与 IDA*、启发式函数、"
           "用哈希表去重，全是数据结构与算法的直接应用。这个项目"
           "就是把算法真正“用出来”的地方。"}}},

        // —— L4：各条线的进阶落点。——
        {"protocols_bus", "通信协议与总线",
         "UART / SPI / I2C / 1-Wire / CAN / Modbus 的电气特性、"
         "时序、寻址与总线仲裁，用逻辑分析仪抓波形对照协议手册。",
         "让多个芯片和模块协同工作——调传感器、显示屏、电机驱动、"
         "多机通信都靠它。",
         "时钟极性 / 相位、地址、应答位这些细节；总线冲突和信号"
         "完整性问题难定位。",
         "network-wired-symbolic", DomainKind::Planned, VerifyMode::Board,
         DomainPriority::Recommended, DomainTrack::Hardware,
         "开发板 + 逻辑分析仪",
         {{"stm32",
           "SPI、I2C、CAN 这些总线要在带完整硬件外设的 MCU 上才练"
           "得起来：STM32 有专门的外设控制器、配套的中断和 DMA "
           "支持，配合逻辑分析仪抓时序，才能真正理解时钟极性、"
           "地址仲裁、应答位这些细节。只用 8051 软件模拟，够玩最"
           "基础的 UART，练不到总线的精髓。"}}},
        {"pcb_design", "EDA · 电路仿真与 PCB 设计",
         "用 EDA 工具（KiCad、立创 EDA、Altium 等）录入原理图，"
         "SPICE 仿真验证关键电路，元件选型与封装，PCB 布局布线，"
         "电源与地平面、DRC 与信号完整性检查，导出 Gerber 打样，"
         "SMT 或手工焊接与上电调试。",
         "把电路从纸面和面包板变成可靠、可批量复制的实物——"
         "做自己的开发板、模块和产品的最后一步。EDA 是这一整套"
         "从设计到制造的软件流水线。",
         "从“能连通”到“稳定可靠”：信号完整性、EMC、可制造性，"
         "每一次打样都有成本和周期。",
         "applications-engineering-symbolic", DomainKind::Planned,
         VerifyMode::Bench, DomainPriority::Recommended, DomainTrack::Hardware,
         "EDA 软件 + 打样 + 焊接",
         {{"stm32",
           "画一块板子是围绕一颗你已经用熟的芯片展开的：每个引脚"
           "接什么、要不要上拉、晶振和去耦电容怎么摆、电源怎么分区，"
           "都建立在“我清楚这颗芯片怎么工作”之上。先在开发板上把 "
           "STM32 用透，自制板才不会只是抄参考设计。"},
          {"electronics_basics",
           "EDA 和 PCB 设计是电路知识的工程化落地：SPICE 仿真要看懂"
           "结果，电源完整性、地平面、去耦、走线阻抗、EMC，每一条"
           "都是模拟电路和信号知识的实际约束。原理图上画错一个"
           "上下拉，板子回来就是废的。"}}},
        {"freertos", "FreeRTOS",
         "任务与调度策略，队列 / 信号量 / 互斥量 / 事件组，"
         "临界区与中断的配合，堆内存管理，优先级反转及其对策。",
         "在单片机上跑多任务：把数据采集、控制、通信拆成互不阻塞"
         "的任务，用调度器统一安排，代码结构比一个大 while 循环"
         "清晰得多。",
         "任务优先级和共享资源的设计；抢占引入的时序问题难复现。",
         "preferences-system-time-symbolic", DomainKind::Planned,
         VerifyMode::Board, DomainPriority::Recommended, DomainTrack::Hardware,
         "开发板 / QEMU",
         {{"stm32",
           "RTOS 不是凭空运行的，它要移植到一个具体的 MCU 上："
           "任务切换依赖该架构的上下文保存方式，SysTick 提供时基，"
           "中断优先级要和内核配合。STM32 加 Cortex-M 是 FreeRTOS "
           "最主流的落地平台。先把裸机 STM32 跑通，再引入调度器，"
           "才看得清 RTOS 到底解决了什么、又带来了多少开销。"}}},
        {"dsp", "数字信号处理",
         "采样与量化、卷积、FIR / IIR 滤波器设计与实现、FFT 与"
         "频谱分析、加窗、重采样，以及定点与实时实现。",
         "把采集回来的信号变得有用：滤掉噪声和工频干扰、提取"
         "频率特征、做包络和相位检测。是音频、振动分析、通信、"
         "雷达、电力监测这些方向的共同工具。既可以在 MCU 上用 "
         "CMSIS-DSP 实时跑，也可以用 FPGA 做成硬件流水线。",
         "时域和频域来回切换需要建立直觉；定点实现要处理溢出和"
         "精度。信号与系统的变换数学作为背景，见下方理论科目。",
         "utilities-system-monitor-symbolic", DomainKind::Planned,
         VerifyMode::Board, DomainPriority::Recommended, DomainTrack::Hardware,
         "开发板（带 FPU/DSP 指令）",
         {{"sensors",
           "信号处理的前提是先有一段采集干净的信号：采样率够不够、"
           "有没有抗混叠、量程和分辨率合不合适，全在信号调理这一"
           "步决定。前端没做好，DSP 只是在放大噪声。"},
          {"stm32",
           "实时 DSP 要在一个有一定算力的平台上做：STM32 的 F4/F7 "
           "带单精度 FPU 和 CMSIS-DSP 库，能实时跑滤波和 FFT。"
           "先熟悉这类芯片的定时器、ADC、DMA，才能搭出“采样—处理—"
           "输出”的实时链路。"}}},
        {"motor_control", "电机控制",
         "有刷 / 无刷直流电机与步进电机的驱动，PWM 与死区，"
         "H 桥与三相桥，电流 / 位置 / 速度反馈，梯形换相到 FOC "
         "（矢量控制），以及 PID 闭环整定。",
         "让电机按你要的转速、位置、力矩运转——机器人、云台、"
         "电动工具、平衡车、无人机的动力核心。是模拟电路、"
         "功率器件、传感器、实时控制和 DSP 数学的综合落地。",
         "强电与弱电混在一起，调试有烧管子的风险；FOC 的坐标变换"
         "和电流环整定门槛较高。控制理论与 PID 作为背景，见下方。",
         "system-run-symbolic", DomainKind::Planned, VerifyMode::Board,
         DomainPriority::Optional, DomainTrack::Hardware,
         "电机 + 驱动板 + 电源",
         {{"stm32",
           "电机控制要用到 STM32 的高级定时器（互补 PWM、死区、"
           "刹车输入）、ADC 与运放采样、以及和 PWM 同步的中断。"
           "这些外设先玩熟，才谈得上写换相和电流环。"},
          {"sensors",
           "闭环控制离不开反馈：电流采样、编码器或霍尔的位置、"
           "有时还有电压和温度。这些信号的调理和标定做不好，"
           "环路就震荡或失步。"},
          {"dsp",
           "FOC 的核心是 Clarke / Park 坐标变换加上电流环滤波，"
           "本质是一组实时信号处理运算；换相噪声、纹波抑制也要用"
           "到滤波器设计的思路。"}}},
        {"embedded_linux", "嵌入式 Linux",
         "交叉编译工具链，Buildroot / Yocto 构建根文件系统，"
         "U-Boot 与内核启动流程，设备树，文件系统与存储，"
         "systemd 与服务，OTA 升级。",
         "当算力和功能需求超过单片机——要跑网络协议栈、图形界面、"
         "数据库、Python——就上带 MMU 的处理器和 Linux。做网关、"
         "工控屏、智能音箱、边缘服务器这类产品的底座。",
         "构建系统庞大、报错晦涩；启动链路长，任何一环出问题都"
         "卡在串口没输出。",
         "drive-harddisk-symbolic", DomainKind::Planned, VerifyMode::Board,
         DomainPriority::Optional, DomainTrack::Systems,
         "SBC（树莓派等）",
         {{"stm32",
           "先在裸机和 RTOS 上做过项目，才看得清完整的 Linux 用"
           "多大的开销（内存、启动时间、实时性）换来了多大的便利"
           "（进程隔离、现成的网络和文件系统、丰富的软件生态）。"
           "这是概念上的对照，不是硬性前置。",
           false}}},
        {"edge_ai", "端侧 AI 部署",
         "模型量化、剪枝与蒸馏，算子与内存约束，嵌入式推理框架"
         "（TFLite Micro、CMSIS-NN 等），在 MCU / SBC 上跑推理"
         "并评估精度损失。",
         "把模型开发和嵌入式两条线接起来：做本地关键词唤醒、"
         "振动异常检测、小图像分类这类不依赖云端的智能设备。",
         "在极其有限的算力和内存下做取舍；量化掉点和实时性之间"
         "的平衡。",
         "applications-science-symbolic", DomainKind::Planned,
         VerifyMode::Board, DomainPriority::Optional, DomainTrack::AI,
         "开发板 / SBC",
         {{"model_dev",
           "端侧部署的前提是先有一个训练好、评估过的模型——知道"
           "它的结构、精度基线、算子构成和参数量，才谈得上量化、"
           "剪枝、蒸馏，以及在有限算力下大概会掉多少点。没有完整"
           "的训练评估流程，端侧优化就没有可对照的基准。"},
          {"stm32",
           "端侧推理的目标平台正是 STM32 这类 MCU：只有几十到"
           "几百 KB 的 RAM，没有 FPU 或只有单精度，要用 CMSIS-NN "
           "或 TFLite Micro 这样为受限环境写的框架。先熟悉这类"
           "平台的内存模型和外设，才谈得上把模型塞进去还能实时跑。"}}},
    };
    return specs;
}

const vector<TheoryTopic>& theory_topics() {
    static const vector<TheoryTopic> topics = {
        {"离散数学",
         "命题与谓词逻辑、集合与关系、图论、组合计数、数学归纳法。",
         "算法正确性证明、复杂度推导的语言；编译原理、形式化方法的基础。"},
        {"计算理论与自动机",
         "正则语言与 DFA/NFA、上下文无关文法、图灵机、可计算性与 P/NP。",
         "理解正则表达式和词法分析的能力边界；判断一个问题能不能算、"
         "好不好算。"},
        {"算法复杂度分析",
         "渐进记号、摊还分析、递归式求解、问题下界与 NP 完全性。",
         "预估程序在大规模数据下的表现，为数据结构和算法选型提供依据。"},
        {"线性代数与概率统计",
         "矩阵运算与分解、向量空间、概率分布、期望与方差、极大似然。",
         "机器学习、信号处理、图形学、控制理论共同的数学底座。"},
        {"信号与系统",
         "连续与离散信号、卷积、傅里叶级数 / 变换、拉普拉斯与 Z 变换、"
         "采样定理、系统的频率响应与稳定性。",
         "数字信号处理和滤波器设计的数学基础，也是控制理论、通信、"
         "图像处理的共同语言。"},
        {"控制理论与 PID",
         "反馈与传递函数、系统稳定性判据、根轨迹与频域法、PID 整定、"
         "状态空间简介。",
         "电机调速与位置伺服、温度 / 压力闭环、平衡车和多旋翼等一切"
         "“测量—比较—执行”的控制类项目。"},
        {"通信原理",
         "调制与解调（ASK/FSK/PSK/QAM）、信道容量、信道编码与纠错、"
         "复用与多址、扩频。",
         "理解 UART/CAN 之上的无线链路（蓝牙、WiFi、LoRa）和高速"
         "有线接口为什么这样设计，排查误码和链路预算问题。"},
        {"模拟电路进阶",
         "运放的非理想特性、噪声与失调、有源滤波器综合、基准与"
         "带隙、电源完整性。",
         "把信号调理、传感器前端、精密测量从“能用”做到“准”。"},
        {"电磁兼容与信号完整性",
         "传输线与反射、串扰、地弹、共模与差模干扰、屏蔽与滤波、"
         "EMC 测试项目。",
         "解释高速 PCB 为什么要控阻抗、加端接、分割地平面，"
         "以及产品过不了 EMC 认证时从哪里下手。"},
        {"体系结构进阶",
         "流水线与冒险、乱序执行、多级缓存与一致性协议、分支预测、SIMD。",
         "解释性能优化为什么有效，指导写出对硬件友好的数据布局和循环。"},
    };
    return topics;
}

// 迭代到不动点求层号：小图、无环，最多 nodes 轮即稳定。成环的节点留在
// 第 0 层。
vector<int> resolve_layers(const vector<vector<int>>& prerequisites) {
    vector<int> layer(prerequisites.size(), 0);
    bool changed = true;
    size_t guard = 0;
    while (changed && guard++ <= prerequisites.size()) {
        changed = false;
        for (size_t i = 0; i < prerequisites.size(); ++i) {
            int want = 0;
            for (const int pre : prerequisites[i]) {
                want = max(want, layer[static_cast<size_t>(pre)] + 1);
            }
            if (want != layer[i]) {
                layer[i] = want;
                changed = true;
            }
        }
    }
    return layer;
}

} // namespace

DomainGraph build_domain_graph(
    const ChapterCatalog& catalog,
    const map<string, int>& mastery_by_id) {
    const auto& specs = domain_specs();
    DomainGraph graph;
    graph.theory = theory_topics();

    map<string, int> index_by_id;
    for (size_t i = 0; i < specs.size(); ++i) {
        index_by_id[specs[i].id] = static_cast<int>(i);
    }

    const auto side_of = [](const char* id) {
        return electronics_ids().count(id) > 0 ? GraphSide::Electronics
                                               : GraphSide::Computer;
    };

    struct ResolvedPrereq {
        int index;
        const char* reason;
        bool strong;
        bool cross;
    };
    vector<vector<ResolvedPrereq>> prereqs(specs.size());
    // 分方向的前置下标，只用于本方向内分层（跨方向关联不参与分层）。
    vector<vector<int>> same_side_prereqs(specs.size());
    for (size_t i = 0; i < specs.size(); ++i) {
        const GraphSide side = side_of(specs[i].id);
        for (const Prereq& pre : specs[i].prerequisites) {
            const auto found = index_by_id.find(pre.id);
            if (found == index_by_id.end()) {
                continue;
            }
            const bool cross = side_of(pre.id) != side;
            prereqs[i].push_back(
                {found->second, pre.reason, pre.strong, cross});
            if (!cross) {
                same_side_prereqs[i].push_back(found->second);
            }
        }
    }

    const vector<int> layer = resolve_layers(same_side_prereqs);

    // 每个方向各自的层数，以及 (方向, 层) 分组的槽位。
    for (size_t i = 0; i < specs.size(); ++i) {
        int& count = side_of(specs[i].id) == GraphSide::Electronics
            ? graph.electronics_layer_count
            : graph.computer_layer_count;
        count = max(count, layer[i] + 1);
    }
    map<pair<int, int>, int> slot_size; // (side, layer) -> 节点数
    for (size_t i = 0; i < specs.size(); ++i) {
        const int s = static_cast<int>(side_of(specs[i].id));
        ++slot_size[{s, layer[i]}];
    }
    map<pair<int, int>, int> slot_fill;

    const auto& catalog_chapters = catalog.chapters();

    graph.nodes.reserve(specs.size());
    for (size_t i = 0; i < specs.size(); ++i) {
        const DomainSpec& spec = specs[i];
        const GraphSide side = side_of(spec.id);
        const int s = static_cast<int>(side);

        DomainNode node;
        node.id = spec.id;
        node.title = spec.title;
        node.content = spec.content;
        node.purpose = spec.purpose;
        node.difficulty = spec.difficulty;
        node.icon = {.type = "theme", .name = spec.icon, .path = ""};
        node.kind = spec.kind;
        node.verify = spec.verify;
        node.priority = spec.priority;
        node.track = spec.track;
        node.side = side;
        node.entry = entry_ids().count(spec.id) > 0;
        node.note = spec.note;
        node.app_id = spec.app_id != nullptr ? spec.app_id : "";
        node.layer = layer[i];
        node.slot = slot_fill[{s, layer[i]}]++;
        node.layer_size = slot_size[{s, layer[i]}];

        const bool has_category =
            catalog_chapters.find(spec.id) != catalog_chapters.end();
        if (node.kind == DomainKind::Available && has_category) {
            for (const auto& category : catalog.categories()) {
                if (category.name == spec.id) {
                    node.title = category.title;
                    node.content = category.description;
                    node.icon = category.icon;
                    break;
                }
            }
            const CategoryProgress progress = aggregate_category_progress(
                catalog, spec.id, mastery_by_id);
            node.total = progress.total;
            node.mastered = progress.mastered;
            node.completion = progress.total > 0
                ? progress.mastery_sum /
                      (static_cast<double>(kMaxMastery) * progress.total)
                : 0.0;
        } else if (node.kind == DomainKind::Available) {
            // 路线图说是已开放，但 catalog 里查无此分类——降级为规划中。
            node.kind = DomainKind::Planned;
        }

        graph.nodes.push_back(std::move(node));
    }

    for (size_t i = 0; i < specs.size(); ++i) {
        for (const auto& pre : prereqs[i]) {
            DomainEdge edge{.from = pre.index,
                            .to = static_cast<int>(i),
                            .reason = pre.reason,
                            .strong = pre.strong,
                            .cross = pre.cross};
            (pre.cross ? graph.cross_edges : graph.edges)
                .push_back(std::move(edge));
        }
    }

    return graph;
}
