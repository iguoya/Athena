#!/usr/bin/env python3
"""按计科 / 电子信息培养要求补全两章：拆掉教法边、补核心课、理由留档不画线。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLARIS = ROOT / "content" / "polaris.json"
CATALOG = ROOT / "content" / "sources" / "catalog.json"


def node_map(entry: dict) -> dict[str, dict]:
    return {node["id"]: node for node in entry["nodes"]}


def drop_edges(entry: dict, pairs: set[tuple[str, str]]) -> list[dict]:
    kept = []
    removed = []
    for edge in entry["edges"]:
        key = (edge["from"], edge["to"])
        if key in pairs:
            removed.append(edge)
        else:
            kept.append(edge)
    entry["edges"] = kept
    return removed


def set_requires(nodes: dict[str, dict], node_id: str, requires: list[str]) -> None:
    nodes[node_id]["requires"] = requires


def main() -> None:
    polaris = json.loads(POLARIS.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    maps = {entry["id"]: entry for entry in polaris["maps"]}
    cs = maps["computer-science"]
    ei = maps["electronic-information"]
    cs_nodes = node_map(cs)
    ei_nodes = node_map(ei)

    # —— 计算机：对照计科培养方案核心课与系统能力目标 ——
    cs_nodes["polaris.cs.operating_systems"]["priority"] = "essential"
    cs_nodes["polaris.cs.operating_systems"]["priority_reason"] = (
        "操作系统是计科培养的专业核心：进程、虚拟内存和并发原语是「能设计实现计算机系统」"
        "这条培养目标的底座，缺了就不构成这个学科。"
    )
    cs_nodes["polaris.cs.computer_networks"]["priority"] = "essential"
    cs_nodes["polaris.cs.computer_networks"]["priority_reason"] = (
        "计算机网络是计科培养方案里的专业核心课，也是「能在互联环境里实现系统」"
        "这条培养目标的直接对应；缺了这一层，学科图就是残的。"
    )
    cs_nodes["polaris.cs.linux_sysprog"]["priority"] = "important"
    cs_nodes["polaris.cs.linux_sysprog"]["priority_reason"] = (
        "培养方案不一定单列这门课，但系统能力目标要落到进程、文件描述符和系统调用上；"
        "它支撑操作系统与网络编程的实现，本身不是另一门核心理论课。"
    )
    cs_nodes["polaris.cs.concurrency"]["priority"] = "important"
    cs_nodes["polaris.cs.concurrency"]["priority_reason"] = (
        "并发是系统能力的深化，操作系统课已经建立概念；单独一门用来把正确的多线程写出"
        "可验证的结果，对培养目标重要，但不是另一条专业核心课。"
    )

    # —— 电子信息：对照电路 / 模电 / 数电 / 信号 / 通信 / 微机 ——
    ei_nodes["polaris.ei.mcu_8051"]["priority"] = "optional"
    ei_nodes["polaris.ei.mcu_8051"]["priority_reason"] = (
        "培养方案里的微机与嵌入式实践，当代平台是 32 位 MCU；51 只作为更缓的入门台阶"
        "保留在图上，避免有人不知道这条老路，但不把它当成 STM32 的闸门。"
    )
    ei_nodes["polaris.ei.dsp"]["priority"] = "essential"
    ei_nodes["polaris.ei.dsp"]["priority_reason"] = (
        "数字信号处理是电子信息培养方案的专业核心，对应「信息获取与处理」这条培养目标；"
        "信号与系统给数学语言，这一门要把滤波和变换做成可验证的实现。"
    )
    ei_nodes["polaris.ei.freertos"]["priority"] = "important"
    ei_nodes["polaris.ei.freertos"]["priority_reason"] = (
        "嵌入式方向实现目标需要多任务与实时调度，但不是所有电子信息核心课都叫 RTOS；"
        "它撑起产品级固件，列在重要档，不从核心课名单里挤掉模电数电通信。"
    )

    unforced_pairs = {
        ("polaris.cs.cpp", "polaris.cs.da"),
        ("polaris.cs.cpp", "polaris.cs.dp"),
        ("polaris.cs.linux_sysprog", "polaris.cs.concurrency"),
        ("polaris.cs.linux_sysprog", "polaris.cs.computer_networks"),
        ("polaris.ei.mcu_8051", "polaris.ei.stm32"),
        ("polaris.ei.stm32", "polaris.ei.pcb_design"),
        ("polaris.ei.sensors", "polaris.ei.dsp"),
        ("polaris.ei.stm32", "polaris.ei.dsp"),
        ("polaris.ei.electronics_basics", "polaris.ei.fpga"),
    }
    removed = drop_edges(cs, unforced_pairs) + drop_edges(ei, unforced_pairs)
    why = {
        ("polaris.cs.cpp", "polaris.cs.da"): "算法思想与语言无关；C++ 是本平台实现课的教学载体，不是知识门槛。",
        ("polaris.cs.cpp", "polaris.cs.dp"): "模式讲的是耦合怎么拆，不绑死在 C++ 上；示例语言不是先修。",
        ("polaris.cs.linux_sysprog", "polaris.cs.concurrency"): "并发原语在 C++ 标准库和 RTOS 里都能练，不必先过 Linux 系统调用。",
        ("polaris.cs.linux_sysprog", "polaris.cs.computer_networks"): "协议本身可以独立学；抓包实现是网络编程那门课的事。",
        ("polaris.ei.mcu_8051", "polaris.ei.stm32"): "51 是 gentler 的入门台阶，不是 STM32 的知识闸门；工程上可以直接上 32 位芯片。",
        ("polaris.ei.stm32", "polaris.ei.pcb_design"): "画板需要的是电路知识，不需要先用熟某一颗 MCU。",
        ("polaris.ei.sensors", "polaris.ei.dsp"): "DSP 是通用方法，可以在仿真里学；干净的前端是应用场景，不是课程门槛。",
        ("polaris.ei.stm32", "polaris.ei.dsp"): "实时 DSP 可以在 PC 或 FPGA 上做；STM32 只是常见落地平台。",
        ("polaris.ei.electronics_basics", "polaris.ei.fpga"): "FPGA 真正的知识门槛是系统的数字电路，不是面包板上的入门电路；先修改挂到数电。",
    }
    for entry, prefix in ((cs, "polaris.cs."), (ei, "polaris.ei.")):
        notes = []
        for edge in removed:
            if edge["from"].startswith(prefix) or edge["to"].startswith(prefix):
                notes.append(
                    {
                        "from": edge["from"],
                        "to": edge["to"],
                        "rationale": edge["rationale"],
                        "why_unforced": why[(edge["from"], edge["to"])],
                    }
                )
        entry["unforced_prereqs"] = notes

    set_requires(cs_nodes, "polaris.cs.da", [])
    set_requires(cs_nodes, "polaris.cs.dp", [])
    set_requires(cs_nodes, "polaris.cs.concurrency", [])
    set_requires(cs_nodes, "polaris.cs.computer_networks", [])
    set_requires(ei_nodes, "polaris.ei.stm32", [])
    set_requires(ei_nodes, "polaris.ei.dsp", [])
    set_requires(ei_nodes, "polaris.ei.pcb_design", ["polaris.ei.electronics_basics"])

    if not any(node["id"] == "polaris.cs.compilers" for node in cs["nodes"]):
        cs["nodes"].extend(CS_NEW_NODES)
        ei["nodes"].extend(EI_NEW_NODES)
        cs["edges"].extend(CS_NEW_EDGES)
        ei["edges"].extend(EI_NEW_EDGES)

    ei_nodes = node_map(ei)
    set_requires(ei_nodes, "polaris.ei.fpga", ["polaris.ei.digital_circuits"])

    def add_theory(entry: dict, topics: list[dict]) -> None:
        names = {topic["name"] for topic in entry.get("theory", [])}
        for topic in topics:
            if topic["name"] not in names:
                entry.setdefault("theory", []).append(topic)

    add_theory(
        ei,
        [
            {
                "name": "电磁场与电磁波",
                "content": "静电场与恒定磁场、时变电磁场、平面波、传输线与波导的基本图像。",
                "role": "电子信息培养里电磁侧的核心语言：射频、天线、高速互连和 EMC 都从这里出发，不建成实践节点是因为验收主要靠推导与仿真而不是一块可交付的板。",
            },
            {
                "name": "信息论与编码",
                "content": "熵与互信息、信道容量、信源编码与信道编码的基本界限。",
                "role": "给通信、压缩和抗干扰一个「理论上能传多少、错多少」的尺子，配合数字通信那门实践课，而不是另一条独立工程线。",
            },
        ],
    )

    cs["summary"] = (
        "计算机科学与技术的完整课程知识图谱，对照培养方案核心课和「能设计实现计算机系统」"
        "的培养目标列课，不按学期链裁图。必需档覆盖程序设计、数据结构、组成、操作系统、"
        "网络、编译、数据库、软件工程与工程实践；重要档补系统能力与科学计算；"
        "可选档列出汇编加深、设计模式、模型开发和信息安全，避免方向课从视野里消失。"
        "C 语言、C++、Python、工程实践都可以单独起步。实线只表示真先修，虚线是渊源来路；"
        "没有连线的课不是被遗忘，是本身就能独立上手。"
    )
    ei["summary"] = (
        "电子信息的完整课程知识图谱，对照培养方案核心课和「电子系统、信息获取与处理、"
        "通信与嵌入式」的培养目标列课。必需档覆盖电路、模电、数电、传感、DSP、数字通信、"
        "STM32 与总线；重要档补 FPGA、PCB、射频、反馈控制、RTOS 与嵌入式 Linux；"
        "51 单片机作为可选入门台阶保留，不是 STM32 的闸门。电路基础可以单独起步。"
        "跨侧依赖（例如先修 C 语言）在节点专页里作为跨图关联列出。"
    )

    existing_ids = {source["id"] for source in catalog["sources"]}
    for source in NEW_SOURCES:
        if source["id"] not in existing_ids:
            catalog["sources"].append(source)

    POLARIS.write_text(json.dumps(polaris, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"computer-science nodes={len(cs['nodes'])} edges={len(cs['edges'])}")
    print(f"electronic-information nodes={len(ei['nodes'])} edges={len(ei['edges'])}")


CS_NEW_NODES = [
    {
        "id": "polaris.cs.compilers",
        "title": "编译技术",
        "track": "systems",
        "stable_definition": "词法与语法分析、抽象语法树、字节码或中间表示、作用域与类型检查，以及一个能跑起来的树遍历解释器。",
        "engineering_role": "把「程序怎么变成机器做的事」从黑盒变成能拆开看的管子。日常不一定写编译器，但读不懂优化为什么改了你的代码、为什么某次未定义行为只在 -O2 爆，多半卡在这一层。",
        "pitfall": "一上来就写工业级后端；先做一个能跑的解释器，再谈寄存器分配。",
        "practice": "按 Crafting Interpreters 做完一个树遍历解释器：扫描、解析、环境、函数与闭包都能跑通一套小测试。",
        "validation": "integration",
        "validation_note": "在开发机上：解释器能跑通官方测试里的作用域、闭包和错误报告用例；对一段自己写的源码能画出 AST 并逐步对照求值结果。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "编译原理是计科培养方案的专业核心课：不懂程序如何变成可执行的表示，组成、系统和语言三条线中间会留一个洞。",
        "targets": ["target-onboard-computer", "target-realtime-software"],
        "app": "",
        "entry": False,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "crafting-interpreters",
                "locator": "扫描、解析、树遍历解释器与闭包",
            },
            {
                "relation": "adapted",
                "source_id": "nuaa-cs",
                "locator": "培养方案中的编译原理方向",
            },
        ],
    },
    {
        "id": "polaris.cs.databases",
        "title": "数据库",
        "track": "engineering",
        "stable_definition": "关系模型与 SQL、事务与隔离级别、索引与查询计划，以及把 SQLite 嵌进本地工具时的模式设计和备份。",
        "engineering_role": "地面侧把试验数据、配置和进度留下来的默认手段。飞控闭环用不上它，测发控台账、回放和本机学习库天天用。",
        "pitfall": "把数据库当万能容器，不谈事务边界和索引；或者在实时链路里塞进一次同步查询。",
        "practice": "用 SQLite 给一套试验记录建模：表结构、事务写入、按时间范围查询，并用 EXPLAIN 看清索引有没有被用上。",
        "validation": "measurement",
        "validation_note": "在开发机上：同一批写入在事务内崩溃后能回滚到一致状态；带索引的范围查询计划不走全表扫描。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "数据库是计科培养方案的专业核心课，对应「能持久化地组织与查询数据」这条培养目标；缺了这一层，学科图只剩会算和会跑的程序。",
        "targets": ["target-digital-intelligence", "target-vehicle-engineering", "target-realtime-control"],
        "app": "",
        "entry": False,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "sqlite-lang",
                "locator": "SQL 语言、事务与 EXPLAIN 查询计划",
            },
            {
                "relation": "adapted",
                "source_id": "nuaa-cs",
                "locator": "培养方案中的数据库方向",
            },
        ],
    },
    {
        "id": "polaris.cs.scientific_computing",
        "title": "科学计算",
        "track": "engineering",
        "stable_definition": "数组与向量化、线性代数例程、数值积分与 ODE、插值与拟合，以及把一次仿真写成可复现脚本。",
        "engineering_role": "GNC、弹道、信号处理和试验对比的工作台：不是推导公式，是把已经写在纸上的模型跑出能对照的数。",
        "pitfall": "用循环手写矩阵乘法却说不清误差从哪来；脚本不能复现就等于没做。",
        "practice": "用 NumPy 复现一道质点弹道或一维传热：固定随机种子与步长，对照解析解或参考实现画出误差曲线。",
        "validation": "benchmark",
        "validation_note": "在开发机上：同一脚本删掉缓存重建后数值结果一致；误差随步长的下降阶与所选积分方法相符。",
        "volatility": "evolving",
        "priority": "important",
        "priority_reason": "仿真、弹道对比和试验数据处理都靠它把模型变成可复核的数；飞行器上运行的代码不由它承担，但地面侧缺了会把分析拖成手工表格。",
        "targets": ["target-gnc", "target-sensing-compute", "target-vehicle-engineering"],
        "app": "",
        "entry": True,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "numpy-absolute-beginners",
                "locator": "数组、向量化与线性代数例程",
            },
            {
                "relation": "adapted",
                "source_id": "buaa-automation",
                "locator": "培养方案中的数值与仿真实践方向",
            },
        ],
    },
    {
        "id": "polaris.cs.software_engineering",
        "title": "软件工程",
        "track": "engineering",
        "stable_definition": "需求与接口怎么写才可测试，变更与配置怎么留痕，评审、缺陷和发布怎么收口；工具链那一门负责「会用锤子」，这一门负责「工程过程不断档」。",
        "engineering_role": "把一个人能跑的程序变成一组人能改、能查、能交付的系统。研制过程要的追溯链在这里合拢。",
        "pitfall": "把过程写成表格却没有一次真实变更走过；或把工具链配置误当成软件工程。",
        "practice": "给一个已有小项目补齐：接口说明、一次带评审记录的变更、缺陷从发现到关闭的轨迹，以及一次可回退的发布。",
        "validation": "review",
        "validation_note": "在开发机上：一个没参与的人能按接口说明改一处行为并跑通测试；任意一次发布都能指回对应变更与缺陷单。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "软件工程是计科工程教育认证的专业核心：培养目标要求能把个人程序变成可变更、可验证、可交付的系统，工具链课代替不了过程本身。",
        "targets": ["target-realtime-software", "target-vehicle-engineering", "target-onboard-computer"],
        "app": "",
        "entry": True,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "nasa-se-handbook",
                "locator": "需求、接口、验证与配置管理相关章节",
            },
            {
                "relation": "adapted",
                "source_id": "uml-gjb5000a",
                "locator": "配置管理与需求管理过程素养",
            },
        ],
    },
    {
        "id": "polaris.cs.security",
        "title": "信息安全",
        "track": "systems",
        "stable_definition": "威胁模型、常见软件弱点、密码学工程用法、认证与访问控制，以及把一次攻击面检查写成可复现的记录。",
        "engineering_role": "计科培养目标里「能对系统的风险作出判断」落在这里。不建成必修核心，是因为多数方案把它放在选修或概论；不列出就会造成「这门学科没有安全」的盲点。",
        "pitfall": "把安全当成工具清单或道德口号；说不清资产、攻击者和失败条件。",
        "practice": "给一个带网络接口的小服务画威胁模型：列出资产与入口，对照常见弱点改掉一处可验证的问题，并写清剩余风险。",
        "validation": "review",
        "validation_note": "在开发机上：改动前后能复现同一条攻击路径被堵住；威胁模型里每一条剩余风险都有对应的不修理由。",
        "volatility": "evolving",
        "priority": "optional",
        "priority_reason": "信息安全是计科知识体系里独立的一块，培养方案常作选修或概论；必须出现在图上消除盲点，但不挤占编译、数据库、操作系统这些专业核心课的必需档。",
        "targets": ["target-realtime-software", "target-digital-intelligence", "target-vehicle-engineering"],
        "app": "",
        "entry": True,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "owasp-top10",
                "locator": "Web 与软件常见弱点分类",
            },
            {
                "relation": "adapted",
                "source_id": "csapp",
                "locator": "程序的机器级表示中与安全相关的部分",
            },
        ],
    },
]

EI_NEW_NODES = [
    {
        "id": "polaris.ei.digital_circuits",
        "title": "数字电路",
        "track": "hardware",
        "stable_definition": "组合逻辑与化简、时序逻辑与状态机、竞争冒险、建立/保持时间，以及用真值表和时序图把一块中规模数字系统说清楚。",
        "engineering_role": "电子信息培养方案把数电和模电并列为核心。电路基础只建立门和触发器的手感，这一门才是「数字系统怎么设计」；FPGA 课是它的可编程落地，代替不了它。",
        "pitfall": "只会默门电路符号；说不清时序约束，仿真过了上板就毛。",
        "practice": "设计一个带同步复位的计数/译码子系统：给出真值表、状态图和时序图，用仿真核对建立时间，再对照冒险现象改一版。",
        "validation": "simulation",
        "validation_note": "在开发机上：全部输入组合的输出与真值表一致；人为制造一处冒险后能在波形上指认，并给出消除办法。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "数字电子技术是电子信息培养方案的专业核心课，对应数字系统这条培养目标；缺了它，FPGA 和微机接口都会变成照抄例程。",
        "targets": ["target-avionics-bus", "target-sensing-compute", "target-onboard-computer"],
        "app": "",
        "entry": False,
        "verify": "bench",
        "requires": ["polaris.ei.electronics_basics"],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "nand2tetris",
                "locator": "布尔逻辑、组合与时序元件的逐级搭建",
            },
            {
                "relation": "adapted",
                "source_id": "art-of-electronics",
                "locator": "数字逻辑、时序与接口部分",
            },
        ],
    },
    {
        "id": "polaris.ei.analog_circuits",
        "title": "模拟电路",
        "track": "hardware",
        "stable_definition": "运放的线性区与饱和、反馈与稳定性、有源滤波、基准与线性电源、从计算值到面包板上测到的偏差。",
        "engineering_role": "传感前端、信号调理和电源不是数字课能代替的：增益、带宽、噪声和失调会直接决定后面 DSP 吃进去的是信号还是干扰。",
        "pitfall": "只背理想运放公式；板上一测，相位裕度和电源抑制对不上。",
        "practice": "在面包板上搭同相放大、一阶有源低通和线性稳压，用示波器量带宽与阶跃，对照手算和 SPICE。",
        "validation": "measurement",
        "validation_note": "在面包板 / 示波器上：增益与截止频率偏差可解释；能指出一处由电源或接地引起的误差来源。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "模拟电子技术是电子信息培养方案的专业核心课，对应模拟系统与信号调理这条培养目标；电路基础只建立仪器手感，真正能设计调理电路要从这里过。",
        "targets": ["target-sensing-compute", "target-realtime-control", "target-avionics-bus"],
        "app": "",
        "entry": False,
        "verify": "bench",
        "requires": ["polaris.ei.electronics_basics"],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "art-of-electronics",
                "locator": "运放、反馈、滤波与电源部分",
            }
        ],
    },
    {
        "id": "polaris.ei.feedback_control",
        "title": "反馈控制",
        "track": "hardware",
        "stable_definition": "被控对象建模、PID 与超前滞后、稳定性的工程判据，以及在仿真或台架上整定一圈「测—比—执行」。",
        "engineering_role": "电机、舵机、温度和姿态都靠闭环才听指挥。控制课的数学在理论科目里，这里要的是能把环路跑稳、能解释超调从哪来。",
        "pitfall": "只会调三个系数却说不清被控对象；仿真能稳、实物振荡。",
        "practice": "在仿真里给一个二阶对象设计 PID，画出阶跃的超调与调节时间；再把同一组参数放到一个有延迟的模型上，说明要改哪一项。",
        "validation": "simulation",
        "validation_note": "在开发机上：标称模型满足约定的超调与调节时间；加入延迟后能指出振荡来自哪一段相位，并给出一版改过的参数。",
        "volatility": "stable",
        "priority": "important",
        "priority_reason": "电子信息的实现目标包含电子系统的动态行为，反馈控制把「测—比—执行」补进图里，避免只会开环电路；它在自动化专业更靠前，所以放在重要档而不是从电子信息核心课名单里挤掉通信和数电。",
        "targets": ["target-gnc", "target-realtime-control", "target-vehicle-engineering"],
        "app": "",
        "entry": True,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "feedback-systems",
                "locator": "反馈、PID 与稳定性的工程讲法",
            },
            {
                "relation": "adapted",
                "source_id": "buaa-automation",
                "locator": "培养方案中的控制理论与运动控制方向",
            },
        ],
    },
    {
        "id": "polaris.ei.digital_comms",
        "title": "数字通信",
        "track": "hardware",
        "stable_definition": "基带波形、调制与解调、误码与链路预算、同步，以及用软件无线电把一条链路从发到收跑通。",
        "engineering_role": "测控、无线遥测和高速有线接口背后是同一套「符号怎么进信道、怎么在噪声里捡回来」。协议课管帧，这一门管物理层为什么会误码。",
        "pitfall": "把通信原理当公式表；没有一条能看频谱、看误码的实验链路。",
        "practice": "用 GNU Radio 搭一条数字调制链路：能看清频谱，能在加噪声后画出误码率随信噪比的变化。",
        "validation": "measurement",
        "validation_note": "在开发机上（SDR 硬件可选）：无噪声时误码为零；加噪声后误码率曲线趋势与所选调制相符。",
        "volatility": "stable",
        "priority": "essential",
        "priority_reason": "通信原理是电子信息培养方案的专业核心，对应「信息传输」这条培养目标；理论科目给公式，这一门要把一条链路从发到收跑通。",
        "targets": ["target-avionics-bus", "target-sensing-compute", "target-vehicle-engineering"],
        "app": "",
        "entry": True,
        "verify": "code",
        "requires": [],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "gnuradio-tutorials",
                "locator": "调制、噪声与误码率测量入门",
            }
        ],
    },
    {
        "id": "polaris.ei.rf_circuits",
        "title": "射频与微波",
        "track": "hardware",
        "stable_definition": "传输线与阻抗、S 参数、匹配网络、滤波器与简单收发前端，以及为什么高速走线不能再当集总电路看。",
        "engineering_role": "雷达前端、遥测射频和高速 PCB 的共同语言。用不上的人不必先学；用上的人没有它只能抄参考设计。",
        "pitfall": "把射频当「更难的模拟」硬套路；不测 S 参数、不谈匹配。",
        "practice": "在仿真里设计一段微带匹配和一个简单带通，导出 S21/S11，说明通带和回波损耗是否达标。",
        "validation": "simulation",
        "validation_note": "在开发机上：匹配网络在中心频率的回波损耗达到约定门限；能指出一处由线宽或介电常数引起的偏差。",
        "volatility": "stable",
        "priority": "important",
        "priority_reason": "高频电子线路是电子信息培养里电磁与通信前端的主干课；列在重要档，避免把射频当成可以不存在的专题，同时不和模电数电通信抢必需档。",
        "targets": ["target-sensing-compute", "target-avionics-bus"],
        "app": "",
        "entry": False,
        "verify": "bench",
        "requires": ["polaris.ei.analog_circuits"],
        "source_refs": [
            {
                "relation": "adapted",
                "source_id": "analog-rf-basics",
                "locator": "传输线、匹配与 S 参数入门",
            }
        ],
    },
]

CS_NEW_EDGES: list[dict] = []

EI_NEW_EDGES = [
    {
        "from": "polaris.ei.electronics_basics",
        "to": "polaris.ei.digital_circuits",
        "relation": "requires",
        "rationale": "数电建立在门、电平和仪器手感上：不会看高低电平、不会用面包板或仿真器核对真值表，状态机只能停留在纸面。",
        "evidence_refs": [
            {
                "relation": "informed",
                "source_id": "art-of-electronics",
                "locator": "从电平与门电路进入组合与时序",
            }
        ],
        "strong": True,
    },
    {
        "from": "polaris.ei.digital_circuits",
        "to": "polaris.ei.fpga",
        "relation": "requires",
        "rationale": "FPGA 就是把数字电路里的门、触发器、译码器和状态机做成可编程的：写 HDL 本质上是在描述一张逻辑电路图。不先掌握组合/时序、建立保持时间和竞争冒险，仿真能过、上板就出问题。",
        "evidence_refs": [
            {
                "relation": "informed",
                "source_id": "ieee-1364-verilog",
                "locator": "Verilog HDL 组合 / 时序与非阻塞赋值",
            }
        ],
        "strong": True,
    },
    {
        "from": "polaris.ei.electronics_basics",
        "to": "polaris.ei.analog_circuits",
        "relation": "requires",
        "rationale": "运放、滤波和电源都建立在分压、RC 和仪器手感之上：不会用示波器看阶跃、不会算直流工作点，模拟电路只能停留在理想公式。",
        "evidence_refs": [
            {
                "relation": "informed",
                "source_id": "art-of-electronics",
                "locator": "从直流与 RC 进入运放与反馈",
            }
        ],
        "strong": True,
    },
    {
        "from": "polaris.ei.analog_circuits",
        "to": "polaris.ei.rf_circuits",
        "relation": "requires",
        "rationale": "射频前端仍然是放大、滤波和阻抗，只是频率高到必须用传输线和 S 参数说话。模拟电路的反馈与噪声没过，匹配网络只能当黑盒抄。",
        "evidence_refs": [
            {
                "relation": "informed",
                "source_id": "analog-rf-basics",
                "locator": "从集总电路过渡到传输线与匹配",
            }
        ],
        "strong": True,
    },
]

NEW_SOURCES = [
    {
        "id": "crafting-interpreters",
        "title": "Crafting Interpreters（免费在线）",
        "url": "https://craftinginterpreters.com/",
        "kind": "textbook",
    },
    {
        "id": "sqlite-lang",
        "title": "SQLite 语言与事务文档",
        "url": "https://www.sqlite.org/lang.html",
        "kind": "official-tutorial",
    },
    {
        "id": "numpy-absolute-beginners",
        "title": "NumPy：绝对初学者指南",
        "url": "https://numpy.org/doc/stable/user/absolute_beginners.html",
        "kind": "official-tutorial",
    },
    {
        "id": "feedback-systems",
        "title": "Feedback Systems（Åström / Murray，免费在线）",
        "url": "https://fbswiki.org/",
        "kind": "textbook",
    },
    {
        "id": "gnuradio-tutorials",
        "title": "GNU Radio 官方教程",
        "url": "https://wiki.gnuradio.org/index.php/Tutorials",
        "kind": "official-tutorial",
    },
    {
        "id": "analog-rf-basics",
        "title": "Analog Devices：RF Basics",
        "url": "https://www.analog.com/en/resources/technical-articles/rf-basics.html",
        "kind": "primary-engineering-documentation",
    },
    {
        "id": "owasp-top10",
        "title": "OWASP Top 10",
        "url": "https://owasp.org/www-project-top-ten/",
        "kind": "official-tutorial",
    },
]


if __name__ == "__main__":
    main()
