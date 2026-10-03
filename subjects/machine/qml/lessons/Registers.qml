import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Flickable {
    width: parent ? parent.width : 800
    height: parent ? parent.height : 600
    contentWidth: width
    contentHeight: col.height + 40
    clip: true
    ScrollBar.vertical: ScrollBar {}

    ColumnLayout {
        id: col
        x: 28
        width: Math.min(parent.width - 56, 1100)
        spacing: 16

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#6c757d"
            text: "DIS Ch.7 §7.1.1–7.1.2 · Intel SDM Vol.1 §3.4.1.1 · System V psABI §3.2.1 · Microsoft x64 calling convention"
        }

        C.Callout {
            kind: "why"
            title: "先猜再点"
            body: "int 变量通常放在 eax，指针放在 rax。那 eax 和 rax 是两个寄存器吗？往 eax 里写一个值，rax 的高 32 位会变成什么？想完再点下面的按钮。"
        }

        C.RegisterView {}

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#212529"
            text: "x86-64 有 16 个通用寄存器，每个 64 位：rax、rbx、rcx、rdx、rsi、rdi、rbp、rsp，以及 r8 到 r15。"
                  + "eax 是 rax 的低 32 位，ax 是低 16 位，al 是最低一个字节——它们是同一个寄存器的不同切法，不是另外的寄存器。"
                  + "r8 到 r15 的切法是在名字后加 d、w、b，例如 r9d 是 r9 的低 32 位。"
        }

        Flow {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
                        "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15", "rip"]
                delegate: Rectangle {
                    required property string modelData
                    width: chip.implicitWidth + 20
                    height: chip.implicitHeight + 10
                    radius: 6
                    color: modelData === "rip" ? "#e0e7ff" : modelData === "rsp" || modelData === "rbp" ? "#fef3c7" : "#e9ecef"
                    Text {
                        id: chip
                        anchors.centerIn: parent
                        text: modelData
                        font.bold: true
                        color: "#212529"
                    }
                }
            }
        }
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#6c757d"
            text: "黄色的 rsp、rbp 约定用来管理栈（rsp 指向栈顶）；rip 是指令指针，指向下一条要执行的指令，程序不能直接往里写。"
        }

        C.CompareRow {
            Layout.fillWidth: true
            leftTitle: "CPU 规定的"
            leftBody: "有 16 个通用寄存器、它们的别名，以及写入时高位怎么处理：32 位写入清零高 32 位，16 位和 8 位写入不动高位。"
            rightTitle: "调用约定规定的"
            rightBody: "第一个整数参数放哪个寄存器：System V（Linux）放 rdi，Windows x64 放 rcx；返回值两边都在 rax。同一个 CPU，不同系统的约定不同。"
        }

        C.Callout {
            kind: "trap"
            title: "常见误区"
            body: "以为 mov eax, ebx 之后 rax 的高 32 位还留着旧值。它们被清零了。"
                  + "想保留旧值，就不能用 32 位写法；用 16 位或 8 位写法才不会碰高位。"
        }

        C.Callout {
            kind: "key"
            title: "要害"
            body: "读汇编时，寄存器名的宽度透露操作数有多宽：典型的编译结果里 int 用 eax 一类的 32 位名字，指针和 long 用 rax 一类的 64 位名字。"
                  + "这是编译结果的常见样子，不是 C 的保证——int 的宽度由实现决定。"
        }

        C.Checkpoint {
            heading: "随堂考核"
            intro: curriculum.exerciseIntro
            questions: curriculum.inClassQuestions
        }
        C.Checkpoint {
            heading: "课后习题"
            questions: curriculum.homeworkQuestions
        }
    }
}
