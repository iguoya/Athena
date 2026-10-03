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
            text: "Beej §5.1 Memory and Variables · C23 6.2.6 Representations of types"
        }

        C.Callout {
            kind: "why"
            title: "先猜再点"
            body: "int 通常不止一字节。这几个字节是挤在相邻格子里，还是可以拆开随便放？想完再点下面的类型。"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: [
                    { id: "char", label: "char  1 字节" },
                    { id: "int", label: "int  常见 4 字节" },
                    { id: "ptr", label: "指针  本机 8 字节" }
                ]
                delegate: Button {
                    required property var modelData
                    text: modelData.label
                    highlighted: kind === modelData.id
                    onClicked: kind = modelData.id
                }
            }
        }

        C.MemoryStrip {
            addressBase: 0x1000
            cellBytes: 1
            values: bytesFor(kind)
            selected: 0
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#212529"
            text: caption(kind)
        }

        C.CompareRow {
            Layout.fillWidth: true
            leftTitle: "Beej 的说法"
            leftBody: "内存是一排编了号的盒子，每格一字节。多字节的值占相邻若干格；sizeof 告诉你占几格。格子从哪一头先放，C 不管。"
            rightTitle: "不要从示意里多读出来"
            rightBody: "下面这排 2a 00 00 00 是本机小端的样子，不是语言保证。把端序讲成 C 的规则，是在自由发挥。"
        }

        C.Callout {
            kind: "key"
            title: "要害"
            body: "先问占几格（sizeof），再问第一格的编号（地址）。名字只是给人看的。Dive Into Systems 第 2 章会再问这几格落在栈、堆还是数据段。"
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

    property string kind: "int"

    function bytesFor(k) {
        if (k === "char")
            return [0x41]
        if (k === "ptr")
            return [0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        return [0x2a, 0x00, 0x00, 0x00]
    }

    function caption(k) {
        if (k === "char")
            return "char c = 'A'; 从 0x1000 起 1 格，值 0x41。sizeof(c) 是 1。"
        if (k === "ptr")
            return "指针自己也是对象：本机 8 格，格子里写着另一个地址。下一章盯这件事。宽度因实现而异，不要背成 C 保证 8。"
        return "int x = 42 占相邻 4 格（本机常见）。图里最低地址先放 0x2a，只是这台机器的端序；Beej 写明字节序由平台决定。"
    }
}
