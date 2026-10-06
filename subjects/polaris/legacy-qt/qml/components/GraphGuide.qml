import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 图谱页自己的读法：理论科目不建节点，编号理由也不该被专页带走。
Rectangle {
    id: root
    required property var edges
    color: "#FFFFFF"
    border.color: "#D8DEDB"
    border.width: 1
    radius: 12
    implicitHeight: Math.min(320, guideColumn.implicitHeight + 28)

    ScrollView {
        anchors.fill: parent
        anchors.margins: 14
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            id: guideColumn
            width: Math.max(0, parent.width - 8)
            spacing: 12

            Text {
                Layout.fillWidth: true
                text: "左侧按计算机、电子信息两科列课。点知识图谱看全图，点知识点进入这一课的详细介绍。实线是真先修，虚线是渊源来路；没有连线的课按培养要求列出，可以单独起步。"
                color: "#52666D"
                wrapMode: Text.WordWrap
                font.pixelSize: 15
                lineHeight: 1.26
            }

            ColumnLayout {
                visible: root.edges.length > 0
                Layout.fillWidth: true
                spacing: 8

                Label { text: "依赖编号（与图上圆点对应）"; font.bold: true }
                Repeater {
                    model: root.edges
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: (modelData.number || "") + ". "
                                + polaris.nodeTitle(modelData.from)
                                + " → "
                                + polaris.nodeTitle(modelData.to)
                                + (modelData.relation === "requires" ? "" : " · 来路，非门槛")
                            color: "#24424B"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.rationale || ""
                            color: "#5A6D72"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 13
                            lineHeight: 1.22
                        }
                    }
                }
            }

            ColumnLayout {
                visible: polaris.selectedMapTheory.length > 0
                Layout.fillWidth: true
                spacing: 8

                Label { text: "理论科目（不建节点）"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: "它们没有可上手验证的实验，所以不在图上占节点；配合教材了解即可。缺了它们，实践课会变成无尺子的操作。"
                    color: "#62777E"
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                    lineHeight: 1.24
                }
                Repeater {
                    model: polaris.selectedMapTheory
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: modelData.name
                            color: "#24424B"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.content
                            color: "#4A5F66"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            lineHeight: 1.22
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "起什么作用：" + modelData.role
                            color: "#62777E"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            lineHeight: 1.22
                        }
                    }
                }
            }
        }
    }
}
