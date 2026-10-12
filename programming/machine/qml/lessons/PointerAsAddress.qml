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
            text: "Beej §5.2 Pointer Types · §5.3 Dereferencing · §5.7 sizeof and Pointers · C23 6.3.2.3"
        }

        Text {
            text: "int i = 42;   int *p;   p = &i;"
            font.family: "Menlo"
            color: "#0a58ca"
        }

        C.MemoryStrip {
            addressBase: 0x1000
            values: [0x2a, 0x00, 0x00, 0x00]
            selected: 0
            pointerName: "i"
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
            text: "上面一排是 i（从 0x1000 起，本机 4 字节）。下面一排是 p（从 0x2000 起），格子里写着 0x1000。解引用 *p 顺着这个编号去碰 i，不是把 42 塞进 p。"
        }

        C.CompareRow {
            Layout.fillWidth: true
            leftTitle: "Beej 的读法"
            leftBody: "p 的类型是 int *，所以格子里的编号被当成一个 int 的起点。sizeof p 是指针自己的宽度，sizeof *p 才是 int。"
            rightTitle: "别这样读"
            rightBody: "「p 里面住着 i」。i 住在 0x1000。p 住在 0x2000。两块对象，靠地址认识。函数要改 i，传的是 &i，见 §5.4。"
        }

        C.Callout {
            kind: "trap"
            title: "常见误区"
            body: "把指针想成装着对象的盒子，p 和 *p 就会混。先问 p 在哪、占几格，再问格子里的值指向谁，最后才解引用。"
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
