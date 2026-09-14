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
            text: "int x = 42;   int *p = &x;"
            font.family: "Menlo"
            color: "#0a58ca"
        }

        C.MemoryStrip {
            addressBase: 0x1000
            values: [0x2a, 0x00, 0x00, 0x00]
            selected: 0
            pointerName: "x"
            pointerIndex: 0
        }

        C.MemoryStrip {
            addressBase: 0x2000
            values: [0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
            selected: 0
            pointerName: "p"
            pointerIndex: 0
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#212529"
            text: "上面一排是 x（从 0x1000 起 4 字节）。下面一排是 p（从 0x2000 起 8 字节），格子里写的是 0x1000。解引用 *p 走这条箭头，不是把 42 塞进 p 里。"
        }

        C.CompareRow {
            Layout.fillWidth: true
            leftTitle: "该这样读"
            leftBody: "p 的类型是 int *，所以 p 里的地址被当成「一个 int 的起点」。sizeof(p) 是指针自己的大小，sizeof(*p) 才是 int。"
            rightTitle: "别这样读"
            rightBody: "「p 里面住着 x」。x 住在 0x1000。p 住在 0x2000。两边是两块对象，靠地址认识。"
        }

        C.Callout {
            kind: "trap"
            title: "常见误区"
            body: "把指针想成装着对象的盒子，p 和 *p 就会混。先问 p 在哪、占几格，再问格子里的值指向谁，最后才解引用。"
        }
    }
}
