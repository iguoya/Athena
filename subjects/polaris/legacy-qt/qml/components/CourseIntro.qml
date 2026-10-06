import QtQuick

// 原 C++ 首页图谱节点介绍：内容 / 用途 / 难点，设备条件作「需要」。
// 字段来自 cpp-roadmap 的 content / purpose / difficulty / note，不得改写成短句。
Column {
    id: root
    required property var node
    property bool light: false
    property bool extras: false
    property int headingSize: 13
    property int bodySize: 15
    property int definitionLines: 0
    property int roleLines: 0
    property int pitfallLines: 0
    property int needLines: 0

    readonly property color headingColor: light ? "#1F6F68" : "#9AD7C8"
    readonly property color bodyColor: light ? "#1B3036" : "#E7F4F0"
    readonly property color pitfallColor: light ? "#8A4B3F" : "#E0A090"

    readonly property var blocks: {
        const n = root.node || {}
        const list = []
        if (n.stable_definition)
            list.push({
                title: "内容",
                body: n.stable_definition,
                tone: root.bodyColor,
                lines: root.definitionLines
            })
        if (n.engineering_role)
            list.push({
                title: "用途",
                body: n.engineering_role,
                tone: root.bodyColor,
                lines: root.roleLines
            })
        if (n.pitfall)
            list.push({
                title: "难点",
                body: n.pitfall,
                tone: root.pitfallColor,
                lines: root.pitfallLines
            })
        if (n.validation_note)
            list.push({
                title: "需要",
                body: n.validation_note,
                tone: root.bodyColor,
                lines: root.needLines
            })
        if (root.extras && n.practice)
            list.push({
                title: "先做什么",
                body: n.practice,
                tone: root.bodyColor,
                lines: 0
            })
        return list
    }

    spacing: 8
    width: parent ? parent.width : 360

    Repeater {
        model: root.blocks
        delegate: Column {
            required property var modelData
            width: root.width
            spacing: 3
            MapText {
                text: modelData.title
                color: modelData.title === "难点" ? modelData.tone : root.headingColor
                font.pixelSize: root.headingSize
                font.weight: Font.DemiBold
            }
            MapText {
                width: parent.width
                text: modelData.body
                color: modelData.tone
                font.pixelSize: root.bodySize
                wrapMode: Text.WordWrap
                lineHeight: 1.32
                lineHeightMode: Text.ProportionalHeight
                maximumLineCount: modelData.lines > 0 ? modelData.lines : 100
                elide: modelData.lines > 0 ? Text.ElideRight : Text.ElideNone
            }
        }
    }
}
