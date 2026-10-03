import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 内存操作数 [base + index*scale + disp] 的有效地址计算器。
//
// 示意内存：从 0x2000 起 8 个 int（每个 4 字节，小端——只是本机示意，不是 C 的保证）。
// 同一条指令同时给出 Intel 和 AT&T 两种写法（ADR 0007）。
// 规则出处：Intel SDM Vol.1 §3.7.5（有效地址）、GNU as 手册 i386-Memory（两种写法的对应）。
Rectangle {
    id: root

    readonly property int baseAddr: 0x2000
    readonly property int baseReg: 0x2000      // rbx
    property int indexValue: 3                 // rcx
    property int scale: 4
    property int disp: 8

    readonly property var ints: [10, 20, 30, 40, 50, 60, 70, 80]
    readonly property int memSize: ints.length * 4
    readonly property string mono: Qt.platform.os === "osx" ? "Menlo"
                                  : Qt.platform.os === "windows" ? "Consolas" : "monospace"

    readonly property int effective: baseReg + indexValue * scale + disp
    readonly property int offset: effective - baseAddr
    readonly property bool inRange: offset >= 0 && offset + 4 <= memSize

    function byteAt(i) {  // 小端：整数的第 k 字节
        return (ints[Math.floor(i / 4)] >> (8 * (i % 4))) & 0xff
    }
    readonly property int loaded: {
        if (!inRange) return 0
        let v = 0
        for (let k = 3; k >= 0; --k) v = v * 256 + byteAt(offset + k)
        return v
    }

    function hex(n, width) {
        let s = n.toString(16).toUpperCase()
        while (s.length < width) s = "0" + s
        return "0x" + s
    }
    function sign(n) { return n < 0 ? " - " + (-n) : " + " + n }

    readonly property string intelText:
        "mov eax, dword ptr [rbx + rcx*" + scale + (disp === 0 ? "" : sign(disp)) + "]"
    readonly property string attText:
        "movl " + (disp === 0 ? "" : disp) + "(%rbx,%rcx," + scale + "), %eax"

    color: "#1c1917"
    radius: 10
    implicitHeight: col.implicitHeight + 28
    Layout.fillWidth: true

    ColumnLayout {
        id: col
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        Text {
            color: "#fde68a"
            font.family: root.mono
            text: "rbx = " + root.hex(root.baseReg, 4) + "（数组起点）"
        }

        // 示意内存：8 个 int，每个 4 个字节格。
        Flow {
            Layout.fillWidth: true
            spacing: 8
            Repeater {
                model: root.ints.length
                delegate: Column {
                    required property int index
                    spacing: 2
                    Text {
                        text: root.hex(root.baseAddr + index * 4, 4)
                        color: "#a8a29e"
                        font.pointSize: 12
                        font.family: root.mono
                    }
                    Row {
                        spacing: 2
                        Repeater {
                            model: 4
                            delegate: Rectangle {
                                required property int index
                                readonly property int cellOffset: parent.parent.index * 4 + index
                                readonly property bool hit: root.inRange
                                    && cellOffset >= root.offset && cellOffset < root.offset + 4
                                width: 38
                                height: 44
                                radius: 4
                                color: hit ? "#14532d" : "#292524"
                                border.width: hit ? 2 : 1
                                border.color: hit ? "#4ade80" : "#57534e"
                                Text {
                                    anchors.centerIn: parent
                                    text: root.hex(root.byteAt(cellOffset), 2).substring(2)
                                    color: "#fafaf9"
                                    font.family: root.mono
                                    font.pointSize: 14
                                }
                            }
                        }
                    }
                }
            }
        }

        // 三个旋钮：index（rcx）、scale、disp。
        GridLayout {
            columns: 2
            columnSpacing: 12
            rowSpacing: 6
            Text { text: "rcx（下标）"; color: "#d6d3d1" }
            Row {
                spacing: 6
                Repeater {
                    model: [0, 1, 2, 3, 5, 7]
                    delegate: Button {
                        required property int modelData
                        text: modelData
                        highlighted: root.indexValue === modelData
                        onClicked: root.indexValue = modelData
                    }
                }
            }
            Text { text: "scale（缩放）"; color: "#d6d3d1" }
            Row {
                spacing: 6
                Repeater {
                    model: [1, 2, 4, 8]
                    delegate: Button {
                        required property int modelData
                        text: modelData
                        highlighted: root.scale === modelData
                        onClicked: root.scale = modelData
                    }
                }
            }
            Text { text: "disp（偏移）"; color: "#d6d3d1" }
            Row {
                spacing: 6
                Repeater {
                    model: [-4, 0, 4, 8, 16]
                    delegate: Button {
                        required property int modelData
                        text: modelData
                        highlighted: root.disp === modelData
                        onClicked: root.disp = modelData
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#fde68a"
            font.family: root.mono
            text: "Intel：" + root.intelText + "\nAT&T： " + root.attText
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#fafaf9"
            font.family: root.mono
            text: "有效地址 = " + root.hex(root.baseReg, 4) + " + " + root.indexValue + "×" + root.scale
                  + root.sign(root.disp) + " = " + root.hex(root.effective, 4)
        }
        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: root.inRange ? "#86efac" : "#fca5a5"
            text: root.inRange
                  ? "从这个地址读 4 个字节（绿框）→ eax = " + root.loaded + "（" + root.hex(root.loaded, 8) + "）"
                  : "这个地址落在示意内存之外。地址计算本身不会被拦：真机上读到的可能是别的数据，也可能因为访问了没映射的地址而出错。"
        }
    }
}
