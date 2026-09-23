#!/usr/bin/env python3
"""给学术层节点写入 stage，按军工筛选改分级，并补电子侧研制链节点。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLARIS = ROOT / "content" / "polaris.json"
CATALOG = ROOT / "content" / "sources" / "catalog.json"

STAGE_PRIORITY = {
    "polaris.cs.python": ("junior", "optional"),
    "polaris.cs.c_lang": ("junior", "essential"),
    "polaris.cs.engineering_practice": ("junior", "essential"),
    "polaris.cs.cpp": ("intermediate", "essential"),
    "polaris.cs.da": ("intermediate", "essential"),
    "polaris.cs.computer_systems": ("intermediate", "essential"),
    "polaris.cs.assembly": ("intermediate", "important"),
    "polaris.cs.operating_systems": ("intermediate", "essential"),
    "polaris.cs.concurrency": ("intermediate", "essential"),
    "polaris.cs.linux_sysprog": ("intermediate", "important"),
    "polaris.cs.computer_networks": ("intermediate", "important"),
    "polaris.cs.network_programming": ("intermediate", "optional"),
    "polaris.cs.dp": ("intermediate", "optional"),
    "polaris.cs.practice": ("senior", "important"),
    "polaris.cs.model_dev": ("senior", "optional"),
    "polaris.ei.electronics_basics": ("junior", "essential"),
    "polaris.ei.mcu_8051": ("junior", "optional"),
    "polaris.ei.analog": ("intermediate", "essential"),
    "polaris.ei.digital": ("intermediate", "essential"),
    "polaris.ei.stm32": ("intermediate", "essential"),
    "polaris.ei.sensors": ("intermediate", "essential"),
    "polaris.ei.protocols_bus": ("intermediate", "essential"),
    "polaris.ei.freertos": ("intermediate", "essential"),
    "polaris.ei.pcb_design": ("intermediate", "important"),
    "polaris.ei.matlab": ("intermediate", "important"),
    "polaris.ei.signals_systems": ("intermediate", "essential"),
    "polaris.ei.fpga": ("intermediate", "essential"),
    "polaris.ei.dsp": ("senior", "essential"),
    "polaris.ei.communications": ("senior", "important"),
    "polaris.ei.control": ("senior", "important"),
    "polaris.ei.electromagnetics": ("senior", "important"),
    "polaris.ei.embedded_linux": ("senior", "optional"),
    "polaris.ei.linux_driver": ("senior", "optional"),
    "polaris.ei.motor_control": ("senior", "optional"),
    "polaris.ei.edge_ai": ("senior", "optional"),
    "polaris.cs.toolchain": ("junior", "essential"),
    "polaris.cs.data-concurrency": ("intermediate", "essential"),
    "polaris.cs.os-network": ("intermediate", "important"),
    "polaris.cs.data-pipeline": ("intermediate", "essential"),
    "polaris.cs.observability": ("senior", "essential"),
    "polaris.cs.integration": ("senior", "important"),
    "polaris.ei.measurement": ("junior", "essential"),
    "polaris.ei.mcu-interfaces": ("intermediate", "essential"),
    "polaris.ei.power-signal": ("intermediate", "important"),
    "polaris.ei.sensor-chain": ("intermediate", "essential"),
    "polaris.ei.dsp-fpga": ("senior", "important"),
    "polaris.ei.board-system": ("senior", "important"),
}

# 阶段理由只回答「这一层该学它」：学科学习顺序，不拿某个岗位当第一句。
STAGE_REASON = {
    "polaris.cs.python": "初级选修：先用脚本把实验步骤写成可重跑的程序，再进系统语言。",
    "polaris.cs.c_lang": "初级主干：先看见内存、指针和寿命，后面的系统课才有落点。",
    "polaris.cs.engineering_practice": "初级主干：进实验室就要能复现构建、测试和版本；完整性检查也折在这里。",
    "polaris.cs.cpp": "中级主干：对象、寿命和抽象已经要能撑起比玩具更大的程序。",
    "polaris.cs.da": "中级主干：不会量复杂度，选结构和算法就没有尺子。",
    "polaris.cs.computer_systems": "中级主干：程序在机器上怎么跑，要在这一层说清。",
    "polaris.cs.assembly": "中级支撑：需要读懂机器时再补，不是日常写程序的主语言。",
    "polaris.cs.operating_systems": "中级主干：调度、内存和隔离是系统课的核心，不是某一款内核的说明书。",
    "polaris.cs.concurrency": "中级主干：多执行流共享状态，这一层才能判断对不对。",
    "polaris.cs.linux_sysprog": "中级支撑：Unix 进程与文件是系统编程的常规作业环境。",
    "polaris.cs.computer_networks": "中级支撑：分层、延迟和可靠性是网络课本身要建立的判断。",
    "polaris.cs.network_programming": "中级台阶：套接字是网络课的实践面，需要写长期运行的端时再补。",
    "polaris.cs.dp": "中级台阶：大型软件结构用得着，不是计科核心课。",
    "polaris.cs.practice": "资深支撑：把前面的课收成别人能复现的作品。",
    "polaris.cs.model_dev": "资深台阶：方向选修，服务分析与检索，不是系统主干。",
    "polaris.ei.electronics_basics": "初级主干：先会用仪器判电平，后面的电路课才有判据。",
    "polaris.ei.mcu_8051": "初级台阶：建立寄存器与中断的手感，不挡住后续微控制器。",
    "polaris.ei.analog": "中级主干：连续量怎么设计和测量，是电子信息的一半。",
    "polaris.ei.digital": "中级主干：离散量怎么同步，FPGA 和处理器外设的真先修。",
    "polaris.ei.stm32": "中级主干：讲这类 MCU 与接口，料号只是教学实例。",
    "polaris.ei.sensors": "中级主干：物理量采不干净，后面处理只是放大误差。",
    "polaris.ei.protocols_bus": "中级主干：分系统之间怎么按时序说话，是电子系统课的接口面。",
    "polaris.ei.freertos": "中级主干：截止期内的调度要在真实内核上测，产品名只是对照物。",
    "polaris.ei.pcb_design": "中级支撑：原理图变成可打样的板，联调才能在下一块板上重现。",
    "polaris.ei.matlab": "中级支撑：先在模型里把信号、控制和数值实验跑通。",
    "polaris.ei.signals_systems": "中级主干：时域和频域之间切换，是后续处理课的尺子。",
    "polaris.ei.fpga": "中级主干：把数字逻辑焊成可综合的并行通路。",
    "polaris.ei.dsp": "资深主干：把信号变成可用特征，并说清计算量。",
    "polaris.ei.communications": "资深支撑：符号怎么进信道再捡回来，不是插网线。",
    "polaris.ei.control": "资深支撑：测—比—执行要可重复；电机课是落地，控制本身要能指认。",
    "polaris.ei.electromagnetics": "资深支撑：场与路的边界，高速走线不再能当集总电路。",
    "polaris.ei.embedded_linux": "资深台阶：带 MMU 的嵌入式系统，不是硬实时的唯一入口。",
    "polaris.ei.linux_driver": "资深台阶：用户态到硬件的另一侧契约，做板级适配时再深入。",
    "polaris.ei.motor_control": "资深台阶：机电伺服的一种落地，不是控制课本身。",
    "polaris.ei.edge_ai": "资深台阶：把模型放到受限设备上，是方向选修。",
    "polaris.cs.toolchain": "初级主干：每次改动都可复现，后面的验证都站在构建与调试上。",
    "polaris.cs.data-concurrency": "中级主干：并发交接要有上界，队列深度就是延迟。",
    "polaris.cs.os-network": "中级支撑：处理机和试验台上的数据链接口。",
    "polaris.cs.data-pipeline": "中级主干：端到端带时标，才能说清时间花在哪一段。",
    "polaris.cs.observability": "资深主干：最坏行为要用实测验收，不能凭体感改系统。",
    "polaris.cs.integration": "资深支撑：他人可复现、可评审的收口，不是起步课。",
    "polaris.ei.measurement": "初级主干：电气联调的每一步都依赖可重复的测量。",
    "polaris.ei.mcu-interfaces": "中级主干：外设与总线是软硬件接口面。",
    "polaris.ei.power-signal": "中级支撑：电源分区和完整性决定联调能不能重现。",
    "polaris.ei.sensor-chain": "中级主干：采集链给出的数字必须能对上物理量。",
    "polaris.ei.dsp-fpga": "资深支撑：板级数据通路接到可验收的特征与吞吐。",
    "polaris.ei.board-system": "资深支撑：合机后看最坏行为，而不是单板均值。",
}

# 学科为什么必须学。第一句是培养方案里的理由，不拿某个岗位当主语。
PRIORITY_REASON = {
    "polaris.cs.python": "脚本、科学计算和数据处理的常用语言，能把实验步骤写成可重跑的程序；不是计科培养的主语言主干，所以放在初级选修。",
    "polaris.cs.c_lang": "能看见内存、指针和资源寿命的系统语言，是操作系统、组成原理和嵌入式共同的地基。",
    "polaris.cs.engineering_practice": "软件要能复现：构建、测试、版本和变更可追溯，这是工程教育里的基础能力，不是某一条生产线的工序。",
    "polaris.cs.cpp": "在不引入垃圾回收停顿的前提下管理对象寿命与抽象，是能把程序做成大型结构的主流系统语言。",
    "polaris.cs.da": "不会分析复杂度与最坏界，选结构和算法就没有尺子；这是计科培养的核心判断。",
    "polaris.cs.computer_systems": "程序在机器上怎么被执行：数的表示、指令、存储层次和中断。缺了它，上层课会变成背步骤。",
    "polaris.cs.assembly": "指令、寄存器和栈帧是读懂机器的语言；日常不必手写，但系统课和调试终究要落到这一层。",
    "polaris.cs.operating_systems": "调度、虚拟内存、并发原语和隔离是计算机系统的核心课，不是某一款实时内核的说明书。",
    "polaris.cs.concurrency": "多个执行流共享状态时什么叫正确，是系统课必须单独建立的判断。",
    "polaris.cs.linux_sysprog": "进程、文件描述符、信号和套接字是 Unix 上写系统程序的基本构件。",
    "polaris.cs.computer_networks": "分层、寻址、可靠传输和延迟从哪一层来，是网络课要建立的判断，不是某一种现场总线手册。",
    "polaris.cs.network_programming": "套接字与超时重试是计算机网络的实践面，不必再单独占主干一格。",
    "polaris.cs.dp": "给大型软件一种可讨论的结构语言；不是计科核心，实时路径也更看重静态与可分析性。",
    "polaris.cs.practice": "把前面的课收成别人能复现的作品，是从会写走到能交付的收口。",
    "polaris.cs.model_dev": "训练、评测和受控问答是方向选修，不替代系统课，也不构成学科主干。",
    "polaris.ei.electronics_basics": "集总电路、仪器和基本波形是电子信息的入门：不会判电平，后面的课没有共同语言。",
    "polaris.ei.mcu_8051": "用较简单的 MCU 建立「外设 = 寄存器 + 中断」的手感，是台阶不是主干。",
    "polaris.ei.analog": "连续量怎么放大、滤波和测量，是电子信息区别于「只会写寄存器」的那一半。",
    "polaris.ei.digital": "组合 / 时序、时钟和建立保持，是数字系统和处理器外设的地基。",
    "polaris.ei.stm32": "时钟树、DMA、ADC 与定时器是当代微控制器课的共同内容；料号只是实例。",
    "polaris.ei.sensors": "把物理量变成可信数字：调理、采样和标定是电子信息的测量核心。",
    "polaris.ei.protocols_bus": "分系统之间按协议按时序交换数据，是电子系统课的接口面。",
    "polaris.ei.freertos": "任务、优先级和共享资源要在真实调度器上观察，这是操作系统课在嵌入式上的对应物。",
    "polaris.ei.pcb_design": "原理图变成可制造、可焊接、可复查的板，是电子实践从台架走向可复现硬件的一步。",
    "polaris.ei.matlab": "矩阵、信号和动态系统的常规数值与仿真环境，电子信息里用来先在模型里做实验。",
    "polaris.ei.signals_systems": "卷积、傅里叶和采样是电子信息的共同语言，不是某一门处理课的附录。",
    "polaris.ei.fpga": "把数字逻辑做成可综合、可上板的并行通路；时序收敛是数字系统课的关键判断。",
    "polaris.ei.dsp": "滤波、变换和定点实现：把信号变成可计算的特征，并说清运算量。",
    "polaris.ei.communications": "调制、噪声、同步和误码：通信课要的是从信道里把符号捡回来，不是插网线。",
    "polaris.ei.control": "测—比—执行、稳定与误差是自动控制和电子系统的共同课，电机只是一种执行器。",
    "polaris.ei.electromagnetics": "场与路的边界、传输线与反射：频率升高后电路直觉会失效，这是电子信息的中间带。",
    "polaris.ei.embedded_linux": "带 MMU 的嵌入式系统：用户态、设备树和网络协议栈，是方向课不是硬实时的唯一入口。",
    "polaris.ei.linux_driver": "字符设备、中断和 DMA 是内核到硬件的契约，做板级适配时才作为主干。",
    "polaris.ei.motor_control": "PWM、电流环与位置环是机电伺服的综合落地，不是控制课本身。",
    "polaris.ei.edge_ai": "把模型量化并放到受限设备上，是智能方向的选修。",
}

# 军工里它还支撑什么。第二句，不能倒过来当裁课理由。
INDUSTRY_REASON = {
    "polaris.cs.python": "试验数据、仿真批跑和事后对比常用它；嵌入式实时路径不靠它运行。",
    "polaris.cs.c_lang": "固件、总线驱动和实时接口仍然用它描述内存与资源上界。",
    "polaris.cs.engineering_practice": "产品保证要求每次提交可复核；交叉编译和完整性检查也折在这里。",
    "polaris.cs.cpp": "地面处理、实时软件和数字后端工具链里，它仍是既能快又能长大的主力。",
    "polaris.cs.da": "有界队列、调度和搜索的最坏延迟，都要先会量复杂度。",
    "polaris.cs.computer_systems": "总线数据、中断和存储层次从这里判读；交叉编译产物也在这一层看。",
    "polaris.cs.assembly": "崩溃现场、启动代码和最坏执行时间要能读寄存器与栈帧。",
    "polaris.cs.operating_systems": "裁剪实时内核、判断隔离和抖动时，用的就是这里的概念。",
    "polaris.cs.concurrency": "控制周期里任务同步和队列交接出不出错，取决于这一层。",
    "polaris.cs.linux_sysprog": "地面站、试验台和处理机大量跑在 Linux 上。",
    "polaris.cs.computer_networks": "试验网和测控要能判断延迟出在哪一层；现场总线是另一套时序。",
    "polaris.cs.network_programming": "上位机和试验台需要长期运行的套接字程序时再补。",
    "polaris.cs.dp": "大型地面工具用得着；实时路径更忌讳多一层间接。",
    "polaris.cs.practice": "分系统交付仍然要别人能复现、能评审。",
    "polaris.cs.model_dev": "只服务地面分析与受控问答，不进入实时控制闭环。",
    "polaris.ei.electronics_basics": "电气联调和传感前端每一步都要能用仪器把电平判清楚。",
    "polaris.ei.mcu_8051": "不挡住后续微控制器，只用来建立手册和时序图的习惯。",
    "polaris.ei.analog": "传感前端、电源和接收通道都建立在连续量设计上。",
    "polaris.ei.digital": "FPGA 和总线控制器写的就是时序电路。",
    "polaris.ei.stm32": "嵌入式计算和接口实验的常见底座，不把某一颗料号当成学科。",
    "polaris.ei.sensors": "探测、试验和状态监测都要求采进来的数对得上物理量。",
    "polaris.ei.protocols_bus": "分系统联调的核心是极性、地址、应答与仲裁能对照手册判读。",
    "polaris.ei.freertos": "截止期内的最坏抖动要在真实调度器上测，不能只在裸机循环里估。",
    "polaris.ei.pcb_design": "从台架走到可复现硬件，板子必须能打样、能过完整性检查。",
    "polaris.ei.matlab": "半实物和控制律之前，先在模型里把周期和接口跑通。",
    "polaris.ei.signals_systems": "探测、通信和闭环都要能在频域上说话。",
    "polaris.ei.fpga": "高速采集和数字后端要把逻辑做成并行通路。",
    "polaris.ei.dsp": "采集变成可用特征时，定点与耗时决定链路能不能跑完。",
    "polaris.ei.communications": "试验、测控和分系统数据要从噪声里捡回来。",
    "polaris.ei.control": "转台、舵面和天线是落地；稳定裕度本身要能判断。",
    "polaris.ei.electromagnetics": "高速数字和测控走线到了一定边沿速率就必须用场的语言。",
    "polaris.ei.embedded_linux": "处理机、试验台和网关常见；硬实时闭环通常另选内核。",
    "polaris.ei.linux_driver": "板级适配才深入；硬实时岗位更常面对裸机外设。",
    "polaris.ei.motor_control": "转台、舵机和天线伺服用得着，主干仍是通用控制。",
    "polaris.ei.edge_ai": "地面监测可以部署；实时控制不以模型推理为闭环。",
}

TITLES = {
    "polaris.ei.stm32": "微控制器与接口",
    "polaris.ei.freertos": "实时内核",
}

NEW_SOURCES = [
    {
        "id": "mit-ocw-6002",
        "title": "MIT OCW 6.002：电路与电子学",
        "url": "https://ocw.mit.edu/courses/6-002-circuits-and-electronics-spring-2007/",
        "kind": "official-tutorial",
    },
    {
        "id": "mit-ocw-6003",
        "title": "MIT OCW 6.003：信号与系统",
        "url": "https://ocw.mit.edu/courses/6-003-signals-and-systems-fall-2011/",
        "kind": "official-tutorial",
    },
    {
        "id": "mit-ocw-6450",
        "title": "MIT OCW 6.450：数字通信原理",
        "url": "https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/",
        "kind": "official-tutorial",
    },
    {
        "id": "matlab-onramp",
        "title": "MathWorks：MATLAB Onramp",
        "url": "https://matlabacademy.mathworks.com/details/matlab-onramp/gettingstarted",
        "kind": "official-tutorial",
    },
    {
        "id": "simulink-onramp",
        "title": "MathWorks：Simulink Onramp",
        "url": "https://matlabacademy.mathworks.com/details/simulink-onramp/slbe",
        "kind": "official-tutorial",
    },
    {
        "id": "mit-ocw-204a",
        "title": "MIT OCW 2.04A：系统与控制",
        "url": "https://ocw.mit.edu/courses/2-04a-systems-and-controls-spring-2013/",
        "kind": "official-tutorial",
    },
    {
        "id": "mit-ocw-6013",
        "title": "MIT OCW 6.013：电磁学与应用",
        "url": "https://ocw.mit.edu/courses/6-013-electromagnetics-and-applications-spring-2009/",
        "kind": "official-tutorial",
    },
]


def node(
    node_id: str,
    title: str,
    track: str,
    definition: str,
    role: str,
    pitfall: str,
    practice: str,
    validation: str,
    note: str,
    volatility: str,
    reason: str,
    targets: list[str],
    verify: str,
    requires: list[str],
    sources: list[tuple[str, str, str]],
    entry: bool = False,
) -> dict:
    stage, priority = STAGE_PRIORITY[node_id]
    return {
        "id": node_id,
        "title": title,
        "track": track,
        "stable_definition": definition,
        "engineering_role": role,
        "pitfall": pitfall,
        "practice": practice,
        "validation": validation,
        "validation_note": note,
        "volatility": volatility,
        "priority": priority,
        "priority_reason": reason,
        "targets": targets,
        "app": "",
        "entry": entry,
        "verify": verify,
        "stage": stage,
        "stage_reason": STAGE_REASON[node_id],
        "requires": requires,
        "source_refs": [
            {"relation": relation, "source_id": source_id, "locator": locator}
            for relation, source_id, locator in sources
        ],
    }


NEW_EI_NODES = [
    node(
        "polaris.ei.analog",
        "模拟电子",
        "hardware",
        "运放的线性区与饱和、反馈与稳定性、偏置与小信号、有源滤波、基准与线性电源、噪声与失调；用仪器把连续量从计算值对到板上测到的数。",
        "电子信息培养里模电和数电并列为核心。电路基础只建立分压、RC 和运放手感，这一门才是「连续量怎么设计、怎么测」。传感前端、信号调理和电源都落在增益、带宽、噪声和失调上——后面数字课吃进去的是信号还是干扰，在这里就决定了。不依赖先会写寄存器，但没有它，调理电路只能抄参考设计，一换传感器就卡住。",
        "非理想特性（有限增益、摆率、失调、有限带宽）会让「理想运放」算出来的电路上板就偏；把线性区公式用到饱和区是最常见的错。",
        "搭同相放大、差分放大和二阶低通，用示波器量带宽与噪声，对照手算解释偏差，并指出一处接地或失调。",
        "measurement",
        "面包板或试验板上：增益与截止频率可测，并能指出一处失调或接地引起的偏差。",
        "stable",
        "连续量怎么设计、怎么测，是电子信息区别于「只会写寄存器」的那一半；研制链上的传感与电源都要它。",
        ["target-sensing-compute", "target-realtime-control", "target-avionics-bus"],
        "bench",
        ["polaris.ei.electronics_basics"],
        [
            ("adapted", "mit-ocw-6002", "运放、反馈与一阶 / 二阶电路"),
            ("adapted", "art-of-electronics", "运放、滤波与电源"),
        ],
    ),
    node(
        "polaris.ei.digital",
        "数字逻辑",
        "hardware",
        "组合逻辑与化简、时序逻辑与状态机、竞争冒险、建立 / 保持时间、时钟域；用真值表和时序图把一块中规模数字系统说清楚。",
        "电子信息培养方案把数电和模电并列为核心。电路基础只建立门和触发器的手感，这一门才是「数字系统怎么设计」。FPGA 课是它的可编程落地，代替不了建立时间和状态机这两层判断；没有它，HDL 只能仿真过、上板翻车。",
        "把时序当组合来写、跨时钟域直接采样，是最常见也最难在仿真里暴露的错。",
        "用 HDL 或逻辑芯片实现计数器与有限状态机，对照仿真波形和板上按键，指出一次建立时间违规时会发生什么。",
        "measurement",
        "仿真波形与板上行为一致，并能指出一处建立 / 保持或时钟域问题。",
        "stable",
        "离散量怎么同步、怎么测，是数字后端和微控制器外设的地基，不能并进电路入门就算盖完。",
        ["target-onboard-computer", "target-sensing-compute", "target-avionics-bus"],
        "board",
        ["polaris.ei.electronics_basics"],
        [
            ("adapted", "nand2tetris", "布尔逻辑、时序元件与指令执行"),
            ("adapted", "ieee-1364-verilog", "组合 / 时序与非阻塞赋值"),
        ],
    ),
    node(
        "polaris.ei.signals_systems",
        "信号与系统",
        "hardware",
        "连续与离散信号、卷积、傅里叶与采样定理、线性时不变系统的频率响应与稳定性；能在时域和频域之间切换判断。",
        "DSP、通信、控制和图像处理的共同尺子：采样够不够、滤波器为什么那样设计、闭环会不会抖，都先在这里说清。它不是 DSP 课的数学附录，而是电子信息的共同语言——缺了它，后面的定点实现只能盲目调参。",
        "变换公式背下来但看不到「系统对哪一段频率做什么」，就会把滤波和采样当成两套互不相干的手续。",
        "对一段采集波形做采样率选择、抗混叠说明和频谱对照，写出这个系统是稳定还是临界，并解释依据。",
        "analysis",
        "同一段信号给出时域波形与频谱，采样与滤波选择有依据，稳定性判断说得清。",
        "stable",
        "电子信息的共同语言，不是 DSP 的数学附录；测控、探测和闭环都要能在频域上说话。",
        ["target-sensing-compute", "target-gnc", "target-realtime-control"],
        "code",
        [],
        [
            ("adapted", "mit-ocw-6003", "卷积、傅里叶与采样"),
            ("see_also", "scipy-signal", "滤波与频谱分析接口"),
        ],
    ),
    node(
        "polaris.ei.matlab",
        "MATLAB 与 Simulink",
        "engineering",
        "矩阵与信号处理工作流、Simulink 连续 / 离散模型、固定步长仿真、代码生成与和台架对时；用可复现的模型而不是一次性脚本。",
        "电子信息里大量实验先在数值环境里做：画频谱、跑动态系统、对照两组时间序列。控制律和半实物台架也常规经过这一层——先在模型里把周期、量纲和接口跑通，再接到板子或实时机。它不是「会用某一个商业软件」的课，是把已经写在纸上的模型跑出能对照的数。",
        "模型能跑不等于能上实时机：求解器、步长、代数环和代码生成限制会在联调时才爆。",
        "用 Simulink 搭一个带传感器噪声的一阶对象加 PID，固定步长跑通，导出一组可对照的时间序列，并说明步长为什么够用。",
        "simulation",
        "固定步长仿真可复现，阶跃响应超调与调节时间有数，模型文件可交给别人重跑。",
        "evolving",
        "仿真、控制和试验数据处理的常规工具链，不是选修插件；半实物之前几乎都要经过这一层。",
        ["target-gnc", "target-realtime-control", "target-vehicle-engineering"],
        "code",
        [],
        [
            ("adapted", "matlab-onramp", "矩阵运算、绘图与脚本工作流"),
            ("adapted", "simulink-onramp", "连续 / 离散模型与仿真步长"),
            ("see_also", "gd-hil", "半实物岗位对 MATLAB/Simulink 的能力样本"),
        ],
    ),
    node(
        "polaris.ei.communications",
        "测控与数据链",
        "hardware",
        "基带波形、调制与解调、信道与误码、帧与同步、链路预算；把符号送进有噪声的信道再捡回来，并能指出错在哪一层。",
        "电子信息培养里通信是专业核心之一。协议课管帧怎么排，这一门管物理层为什么会误码：弱场、多径、时钟漂了，要有排查步骤，而不是理解成「插上网线」。试验网、测控和分系统数据链用的是同一套判断。",
        "把通信理解成接线或套接字，一旦信道变差就没有下一层可查。",
        "搭一条带噪声的数字链路（仿真或开发板），画出误码率随信噪比的变化，并标出同步失锁条件。",
        "measurement",
        "误码率曲线方向与预期一致，能指出一次失步是帧、时钟还是信道引起的。",
        "stable",
        "研制链上的天地 / 台架数据要能从噪声里捡回来；这是通信传输，不是总线插针。",
        ["target-vehicle-engineering", "target-realtime-software", "target-avionics-bus"],
        "code",
        ["polaris.ei.signals_systems"],
        [
            ("adapted", "mit-ocw-6450", "数字调制、噪声与误码"),
            ("see_also", "cmse-ttc-2023", "测控通信系统的跟踪、遥测与遥控职责"),
        ],
    ),
    node(
        "polaris.ei.control",
        "反馈控制",
        "hardware",
        "被控对象建模、测—比—执行、PID 与超前滞后、稳定性的工程判据；在仿真或台架上整定一圈可重复的闭环。",
        "电机、舵机、温度和姿态都靠闭环才听指挥。控制课的数学可以在理论科目里加深，这里要的是能把环路跑稳、能解释超调从哪来。电机课是它的一种落地，代替不了「稳定裕度」本身。",
        "把 PID 当成三个旋钮乱拧，对象一变或延迟一加就散。",
        "对一个有延迟的一阶对象整定 PID，给出超调、调节时间和抗扰恢复，并说明为什么这组参数能稳住。",
        "measurement",
        "阶跃与扰动两次实验的超调、调节时间可重复，参数选择说得清。",
        "stable",
        "GNC 和测发控闭环的入场判断；电机课是它的一种落地，控制本身要能单独指认。",
        ["target-gnc", "target-realtime-control", "target-robot-systems"],
        "code",
        ["polaris.ei.signals_systems"],
        [
            ("adapted", "mit-ocw-204a", "反馈、稳定性与基本控制器"),
            ("see_also", "matlab-onramp", "用模型观察阶跃与扰动"),
        ],
    ),
    node(
        "polaris.ei.electromagnetics",
        "电磁与传输线",
        "hardware",
        "场与路的边界、传输线与反射、特征阻抗与端接、辐射的来源；高速走线和接口为什么不能再当集总电路。",
        "频率升高以后，走线是有延迟和反射的——这是电子信息从电路课走到高速数字、射频入门之前的中间带。给 PCB 阻抗、端接和辐射一个物理理由，避免把 EMC 规则背成口诀。不展开天线阵或微波网络的专业课深度。",
        "频率升高后仍用直流电路直觉，反射和串扰会看起来像「板子抽风」。",
        "对一段受控阻抗走线计算特征阻抗与端接，用仿真或时域反射说明一次失配造成的台阶，并指出反射从哪来。",
        "analysis",
        "阻抗与端接有计算，失配波形或仿真能对应到反射原因。",
        "stable",
        "高速数字和测控接口到了一定边沿速率就必须用场的语言；这是中间带能力，不是射频专业全集。",
        ["target-avionics-bus", "target-sensing-compute", "target-onboard-computer"],
        "bench",
        ["polaris.ei.electronics_basics"],
        [
            ("adapted", "mit-ocw-6013", "传输线、反射与场路边界"),
            ("see_also", "emc-ott", "高速电路的反射、串扰与接地"),
        ],
    ),
]


def edge(from_id: str, to_id: str, relation: str, rationale: str, source_id: str, locator: str, strong: bool) -> dict:
    return {
        "from": from_id,
        "to": to_id,
        "relation": relation,
        "rationale": rationale,
        "evidence_refs": [{"relation": "informed", "source_id": source_id, "locator": locator}],
        "strong": strong,
    }


NEW_EDGES = [
    edge(
        "polaris.ei.electronics_basics",
        "polaris.ei.analog",
        "requires",
        "模拟电子是电路入门之后把连续量设计到可测：运放、偏置和噪声都建立在分压、RC 和仪器使用之上。",
        "mit-ocw-6002",
        "运放、反馈与一阶 / 二阶电路",
        True,
    ),
    edge(
        "polaris.ei.electronics_basics",
        "polaris.ei.digital",
        "requires",
        "数字逻辑把电路入门里的门和触发器收成可验证的时序系统；没有建立 / 保持和时钟，FPGA 和总线控制器没有判断语言。",
        "nand2tetris",
        "布尔逻辑、时序元件与指令执行",
        True,
    ),
    edge(
        "polaris.ei.analog",
        "polaris.ei.sensors",
        "requires",
        "信号调理是模拟电子的直接应用：增益、抗混叠和基准决定采进来的数是不是物理量。",
        "analog-devices-sensor",
        "传感器接口与信号调理",
        True,
    ),
    edge(
        "polaris.ei.digital",
        "polaris.ei.fpga",
        "requires",
        "写 HDL 是在描述时序电路；不先掌握状态机、时钟和建立 / 保持，综合过、上板也会在时序上翻车。",
        "ieee-1364-verilog",
        "Verilog HDL 组合 / 时序与非阻塞赋值",
        True,
    ),
    edge(
        "polaris.ei.electronics_basics",
        "polaris.ei.stm32",
        "requires",
        "微控制器的每个引脚仍是一段电路：上下拉、去耦、电平和回流路径不清楚，外设寄存器写对了现象也会不对。",
        "art-of-electronics",
        "分压、RC、运放与数字逻辑入门部分",
        True,
    ),
    edge(
        "polaris.ei.signals_systems",
        "polaris.ei.communications",
        "requires",
        "调制、误码和同步都建立在信号、频谱和线性系统之上；没有这把尺子，链路预算只能背公式。",
        "mit-ocw-6003",
        "卷积、傅里叶与采样",
        True,
    ),
    edge(
        "polaris.ei.signals_systems",
        "polaris.ei.control",
        "requires",
        "反馈能不能稳住，先要会看频率响应和稳定性；控制不是三个旋钮，是系统动态。",
        "mit-ocw-6003",
        "线性时不变系统与稳定性",
        True,
    ),
    edge(
        "polaris.ei.matlab",
        "polaris.ei.control",
        "enables",
        "用模型把对象、延迟和控制器放在同一时间轴上，整定和半实物之前能先看到超调与振荡，不是入学门槛。",
        "simulink-onramp",
        "连续 / 离散模型与仿真步长",
        False,
    ),
    edge(
        "polaris.ei.electronics_basics",
        "polaris.ei.electromagnetics",
        "requires",
        "场与路的分界要从集总电路的失效处讲起：走线不再能当电阻，反射才解释得清。",
        "mit-ocw-6013",
        "传输线、反射与场路边界",
        True,
    ),
    edge(
        "polaris.ei.signals_systems",
        "polaris.ei.dsp",
        "requires",
        "滤波、FFT 和定点实现是信号与系统落到可跑代码上的那一步；变换数学不清楚，定点只是在放大噪声。",
        "mit-ocw-6003",
        "卷积、傅里叶与采样",
        True,
    ),
]


def main() -> None:
    polaris = json.loads(POLARIS.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    known_sources = {item["id"] for item in catalog["sources"]}
    for source in NEW_SOURCES:
        if source["id"] not in known_sources:
            catalog["sources"].append(source)
            known_sources.add(source["id"])

    for entry in polaris["maps"]:
        if entry.get("view_kind") != "academic":
            continue
        if entry["id"] == "computer-science":
            entry["summary"] = (
                "计算机科学与技术的课程图。必要性先写这门课在学科里为什么必须学，"
                "再兼顾军工里它还支撑什么，不按单一岗位的业务裁课。"
                "阶段按顺序解锁：初级没打完不上中级，中级没打完不上资深。"
                "初级：C 语言、工程实践。中级：系统基础、操作系统、并发、C++、数据结构、网络。"
                "资深：可复现的交付。Python、设计模式是选修。C 语言、C++、工程实践是入门起点。"
            )
        elif entry["id"] == "electronic-information":
            entry["summary"] = (
                "电子信息的课程图。必要性先写这门课在学科里为什么必须学，"
                "再兼顾军工里它还支撑什么，不按单一岗位的业务裁课。"
                "阶段按顺序解锁：初级没打完不上中级，中级没打完不上资深。"
                "初级：电路基础进实验室。中级：模电、数电、微控制器与接口、总线、实时内核、FPGA、信号与系统。"
                "资深：DSP、通信、反馈控制、电磁与传输线。"
                "电路基础是入门起点。51 单片机是台阶，不挡住微控制器。"
            )

        nodes = entry.setdefault("nodes", [])
        existing = {node["id"] for node in nodes}
        if entry["id"] == "electronic-information":
            for extra in NEW_EI_NODES:
                if extra["id"] not in existing:
                    nodes.append(extra)
                    existing.add(extra["id"])

        for node in nodes:
            node_id = node["id"]
            if node_id in TITLES:
                node["title"] = TITLES[node_id]
            if node_id in STAGE_PRIORITY:
                stage, priority = STAGE_PRIORITY[node_id]
                node["stage"] = stage
                node["priority"] = priority
            if node_id in STAGE_REASON:
                node["stage_reason"] = STAGE_REASON[node_id]
            if node_id in PRIORITY_REASON:
                node["priority_reason"] = PRIORITY_REASON[node_id]
            if node_id in INDUSTRY_REASON:
                node["industry_reason"] = INDUSTRY_REASON[node_id]
            for extra in NEW_EI_NODES:
                if extra["id"] != node_id:
                    continue
                for key in ("stable_definition", "engineering_role", "pitfall",
                            "practice", "validation_note"):
                    node[key] = extra[key]
                break
            if node_id == "polaris.ei.stm32":
                node["requires"] = ["polaris.ei.electronics_basics"]
            if node_id == "polaris.ei.sensors":
                requires = list(node.get("requires") or [])
                if "polaris.ei.analog" not in requires:
                    requires.append("polaris.ei.analog")
                node["requires"] = requires
            if node_id == "polaris.ei.fpga":
                requires = list(node.get("requires") or [])
                if "polaris.ei.digital" not in requires:
                    requires.append("polaris.ei.digital")
                node["requires"] = requires
            if node_id == "polaris.ei.dsp":
                requires = list(node.get("requires") or [])
                if "polaris.ei.signals_systems" not in requires:
                    requires.append("polaris.ei.signals_systems")
                node["requires"] = requires

        if entry["id"] == "electronic-information":
            edges = entry.setdefault("edges", [])
            for item in edges:
                if item.get("from") == "polaris.ei.mcu_8051" and item.get("to") == "polaris.ei.stm32":
                    item["relation"] = "enables"
                    item["strong"] = False
            seen = {(item["from"], item["to"], item["relation"]) for item in edges}
            for extra in NEW_EDGES:
                key = (extra["from"], extra["to"], extra["relation"])
                if key not in seen:
                    edges.append(extra)
                    seen.add(key)

        missing_stage = [node["id"] for node in nodes if not node.get("stage")]
        if missing_stage:
            raise SystemExit("这些节点还没有 stage：" + ", ".join(missing_stage))

    POLARIS.write_text(json.dumps(polaris, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("updated polaris.json and catalog.json")


if __name__ == "__main__":
    main()
