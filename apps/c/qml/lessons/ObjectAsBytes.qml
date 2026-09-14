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

        C.Callout {
            kind: "why"
            title: "先猜再点"
            body: "int x = 42 按小端放进四个字节。最低地址那一格是 2a，还是 00？想完再点下面的类型按钮。"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: [
                    { id: "char", label: "char  1 字节" },
                    { id: "int", label: "int  4 字节" },
                    { id: "ptr", label: "指针  8 字节" }
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
            leftTitle: "C 的说法"
            leftBody: "int x = 42; 的意思是：在某个地址放 4 个字节，按小端写成 2a 00 00 00。x 是这块内存的名字。"
            rightTitle: "常见错觉"
            rightBody: "以为 x 是一个漂在语言里的「值盒子」，跟地址无关。于是 &x、sizeof(x) 都变成要背的符号。"
        }

        C.Callout {
            kind: "key"
            title: "要害"
            body: "sizeof 问的是「占几格」，不是「这个名字有多重要」。换类型时格子数跟着变，名字还叫 x。"
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
            return "char c = 'A';  从 0x1000 起 1 个字节，值 0x41。sizeof(c) 是 1。"
        if (k === "ptr")
            return "64 位下指针本身也是对象：8 个字节，里面写着另一个地址。下一章「指针」盯这件事。"
        return "最低地址先放 0x2a。四个格子是同一对象的四个房间，不是四个变量。"
    }
}
