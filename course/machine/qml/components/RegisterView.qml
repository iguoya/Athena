import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// x86-64 通用寄存器 rax：八个字节格 + 别名选择 + 「写入不同宽度」的演示。
//
// 要让人看见的两件事（Intel SDM Vol.1 §3.4.1.1）：
//   1. eax / ax / al / ah 只是 rax 的一部分，不是另外的寄存器；
//   2. 写 32 位会把高 32 位清零（零扩展），写 16 位、8 位则不动高位。
// 值用 16 位十六进制字符串保存：QML 的数字是 double，装不下 64 位整数。
Rectangle {
    id: root

    // 演示用的两个寄存器初值：rax 被写之前的样子，和写入来源 rbx。
    property string raxStart: "1122334455667788"
    property string rbxValue: "AABBCCDDEEFF0011"

    // 当前选的别名（只做高亮）与写入宽度（做演示）。
    property string alias: "rax"
    property int writeBits: 0  // 0 = 还没写；64 / 32 / 16 / 8

    readonly property string mono: Qt.platform.os === "osx" ? "Menlo"
                                  : Qt.platform.os === "windows" ? "Consolas" : "monospace"

    // 别名 → 它覆盖 rax 的哪些字节（0 是最低字节）。
    readonly property var aliasBytes: ({
        "rax": [0, 1, 2, 3, 4, 5, 6, 7],
        "eax": [0, 1, 2, 3],
        "ax": [0, 1],
        "al": [0],
        "ah": [1]
    })

    function hexByte(hex, byteIndex) {  // byteIndex 0 = 最低字节
        const start = 16 - 2 * (byteIndex + 1)
        return hex.substring(start, start + 2)
    }

    // 把 rbx 的低 bits 位写进 rax，返回 16 位十六进制。
    function written(bits) {
        const n = bits / 4  // 十六进制位数
        const low = rbxValue.substring(16 - n)
        if (bits === 64)
            return rbxValue
        if (bits === 32)
            return "00000000" + low               // 零扩展
        return raxStart.substring(0, 16 - n) + low // 16 / 8 位：高位保持原样
    }

    readonly property string raxNow: writeBits === 0 ? raxStart : written(writeBits)

    // 某个字节在这次写入里的命运：写入 / 被清零 / 没动。
    function fate(byteIndex) {
        if (writeBits === 0)
            return "none"
        const touched = writeBits / 8
        if (byteIndex < touched)
            return "written"
        if (writeBits === 32)
            return "zeroed"
        return "kept"
    }

    function intel(bits) {
        const d = { 64: "mov rax, rbx", 32: "mov eax, ebx", 16: "mov ax, bx", 8: "mov al, bl" }
        return d[bits]
    }
    function att(bits) {
        const d = { 64: "movq %rbx, %rax", 32: "movl %ebx, %eax", 16: "movw %bx, %ax", 8: "movb %bl, %al" }
        return d[bits]
    }

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
            text: "rax = 0x" + root.raxNow
            color: "#fde68a"
            font.family: root.mono
        }

        // 八个字节格，高字节在左（和写十六进制的习惯一致）。
        Row {
            spacing: 6
            Repeater {
                model: 8
                delegate: Rectangle {
                    required property int index
                    readonly property int byteIndex: 7 - index
                    readonly property bool inAlias: root.aliasBytes[root.alias].indexOf(byteIndex) >= 0
                    readonly property string fate: root.fate(byteIndex)
                    width: 62
                    height: 74
                    radius: 6
                    color: fate === "written" ? "#14532d"
                         : fate === "zeroed" ? "#7f1d1d"
                         : "#292524"
                    border.width: inAlias ? 3 : 1
                    border.color: inAlias ? "#fbbf24" : "#57534e"
                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: root.hexByte(root.raxNow, byteIndex)
                            color: "#fafaf9"
                            font.family: root.mono
                            font.bold: true
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "字节 " + byteIndex
                            color: "#a8a29e"
                            font.pointSize: 12
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#d6d3d1"
            text: "黄框是当前别名覆盖的字节。选别名：" + root.alias
                  + (root.alias === "ah" ? "（高 8 位那一字节，只有 ax、bx、cx、dx 才有）" : "")
        }
        Row {
            spacing: 8
            Repeater {
                model: ["rax", "eax", "ax", "al", "ah"]
                delegate: Button {
                    required property string modelData
                    text: modelData
                    highlighted: root.alias === modelData
                    onClicked: root.alias = modelData
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#44403c" }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#d6d3d1"
            text: "写入演示：rax 起初是 0x" + root.raxStart + "，rbx 是 0x" + root.rbxValue
                  + "。把 rbx 的低几位拷进 rax？先想结果，再点。"
        }
        Row {
            spacing: 8
            Repeater {
                model: [64, 32, 16, 8]
                delegate: Button {
                    required property int modelData
                    text: "写 " + modelData + " 位"
                    highlighted: root.writeBits === modelData
                    onClicked: root.writeBits = modelData
                }
            }
            Button {
                text: "复位"
                onClicked: root.writeBits = 0
            }
        }
        Text {
            visible: root.writeBits !== 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#fde68a"
            font.family: root.mono
            text: "Intel：" + root.intel(root.writeBits) + "\nAT&T： " + root.att(root.writeBits)
        }
        Text {
            visible: root.writeBits !== 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#d6d3d1"
            text: "绿色是被写入的字节，红色是被清零的高位，灰色没动。"
                  + (root.writeBits === 32 ? "32 位写入会把高 32 位清零。" : "")
                  + (root.writeBits === 16 || root.writeBits === 8 ? "16 位、8 位写入不碰高位。" : "")
        }
    }
}
