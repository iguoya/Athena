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
            text: "DIS Ch.7 §7.1.3–7.1.5 · Intel SDM Vol.1 §3.7.5 · GNU as 手册 i386-Variations、i386-Memory"
        }

        C.Callout {
            kind: "why"
            title: "先猜再点"
            body: "mov eax, dword ptr [rbx + rcx*4 + 8] 里，方括号里算出来的是一个数，还是一个地址？eax 最后拿到的又是什么？想完再拨下面的旋钮。"
        }

        C.OperandLab {}

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#212529"
            text: "一条指令由操作码和操作数组成。操作数只有三种形式：常数（一个写死的数）、寄存器、内存。"
                  + "内存操作数写成 基址 + 下标×缩放 + 偏移：基址和下标是两个寄存器里的值，缩放只能取 1、2、4、8，偏移是常数；"
                  + "三项可以缺。这个和的结果是一个地址，指令再去那个地址读写数据。"
        }

        C.CompareRow {
            Layout.fillWidth: true
            leftTitle: "Intel 写法"
            leftBody: "目标在前、源在后。寄存器和常数不带前缀；内存用方括号，宽度写在操作数前："
                      + "mov eax, dword ptr [rbx + rcx*4 + 8]"
            rightTitle: "AT&T 写法"
            rightBody: "源在前、目标在后。寄存器带 %，常数带 $；内存写成 偏移(基址,下标,缩放)，宽度写在指令后缀上："
                      + "movl 8(%rbx,%rcx,4), %eax"
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#6c757d"
            text: "Linux 的 GCC、GDB、objdump 默认输出 AT&T；Windows 的文档和 Intel 手册用 Intel。两种写法汇编出来是同一条指令，"
                  + "本应用的实验里 System V 目标默认 AT&T、Windows 目标默认 Intel（ADR 0007）。后缀 b、w、l、q 分别表示 1、2、4、8 字节。"
        }

        C.Callout {
            kind: "trap"
            title: "常见误区"
            body: "把方括号里的东西当成「值」。方括号里算出来的是地址，指令再去读那个地址上的数据。"
                  + "有一条指令只算地址、不读内存：lea（Intel SDM：计算第二个操作数的有效地址，存进第一个操作数）。后面的课会用到它。"
        }

        C.Callout {
            kind: "key"
            title: "要害"
            body: "三条限制：常数不能当目的操作数；一条指令不能同时拿内存当源和目的——mov 不能两头都是内存，要先经过寄存器；"
                  + "缩放因子只有 1、2、4、8。读汇编时先认出每个操作数是哪种形式，再算它的值。"
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
