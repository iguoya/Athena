import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var node
    required property var edges
    signal closed()
    color: "#FFFFFF"
    border.color: "#D8DEDB"
    border.width: 1

    readonly property bool hasNode: Boolean(root.node && root.node.id)

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            x: 22
            width: Math.max(0, parent.width - 44)
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: root.hasNode ? "节点说明" : "如何阅读"
                    color: "#1A313A"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                ToolButton { visible: root.hasNode; text: "×"; onClicked: root.closed() }
            }

            Text {
                visible: !root.hasNode
                Layout.fillWidth: true
                text: "主干看实时与高性能的软、硬件边界。四院十七所的实时控制总体放在重要参考；机器人放在相邻参考。大模型只在助力方向，不进飞控。"
                color: "#52666D"
                wrapMode: Text.WordWrap
                font.pixelSize: 16
                lineHeight: 1.28
            }

            ColumnLayout {
                visible: root.hasNode
                Layout.fillWidth: true
                spacing: 12
                Text {
                    Layout.fillWidth: true
                    text: root.node.title || ""
                    color: "#152D36"
                    wrapMode: Text.WordWrap
                    font.pixelSize: 25
                    font.weight: Font.DemiBold
                }
                Rectangle { Layout.fillWidth: true; height: 4; radius: 2; color: atlas.trackColor(root.node.track || "") }
                Text {
                    text: atlas.priorityLabel(root.node.priority_tier || "") + " · " + atlas.volatilityLabel(root.node.volatility || "") + " · " + atlas.validationLabel(root.node.validation || "")
                    color: "#50656C"
                    font.pixelSize: 14
                }
                Label { text: "它是什么"; font.bold: true }
                Text { Layout.fillWidth: true; text: root.node.stable_definition || ""; wrapMode: Text.WordWrap; color: "#40545B"; font.pixelSize: 16; lineHeight: 1.24 }
                Label { text: "工程中解决什么"; font.bold: true }
                Text { Layout.fillWidth: true; text: root.node.engineering_role || ""; wrapMode: Text.WordWrap; color: "#40545B"; font.pixelSize: 16; lineHeight: 1.24 }
                Label { visible: Boolean(root.node.kit && root.node.kit.reading); text: "读什么"; font.bold: true }
                Text {
                    visible: Boolean(root.node.kit && root.node.kit.reading)
                    Layout.fillWidth: true
                    text: (root.node.kit && root.node.kit.reading) || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }
                Label { visible: Boolean(root.node.kit && root.node.kit.tooling); text: "用什么"; font.bold: true }
                Text {
                    visible: Boolean(root.node.kit && root.node.kit.tooling)
                    Layout.fillWidth: true
                    text: (root.node.kit && root.node.kit.tooling) || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }
                Label { visible: Boolean(root.node.kit && root.node.kit.artifact); text: "交出什么"; font.bold: true }
                Text {
                    visible: Boolean(root.node.kit && root.node.kit.artifact)
                    Layout.fillWidth: true
                    text: (root.node.kit && root.node.kit.artifact) || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }
                Label { text: "先做什么"; font.bold: true }
                Text { Layout.fillWidth: true; text: root.node.practice || ""; wrapMode: Text.WordWrap; color: "#40545B"; font.pixelSize: 16; lineHeight: 1.24 }
                Label { text: "如何验证"; font.bold: true }
                Text { Layout.fillWidth: true; text: root.node.validation_note || ""; wrapMode: Text.WordWrap; color: "#40545B"; font.pixelSize: 16; lineHeight: 1.24 }
                Label { text: "来源"; font.bold: true }
                Repeater {
                    model: root.node.source_refs || []
                    delegate: Text {
                        required property var modelData
                        Layout.fillWidth: true
                        text: "• " + modelData.source_id + " · " + modelData.locator
                        color: "#55727A"
                        wrapMode: Text.WordWrap
                        font.pixelSize: 14
                    }
                }
            }
        }
    }
}
