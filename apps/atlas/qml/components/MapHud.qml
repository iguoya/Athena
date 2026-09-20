import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 贴在地图底部的仪器盘：能力域、分层滤镜、理论科目。不抢图谱高度。
Rectangle {
    id: root
    required property var nodes
    required property var theory
    property string layerFilter: ""
    signal layerChosen(string layerId)
    signal theoryChosen(var item)

    height: hudColumn.implicitHeight + 22
    radius: 18
    color: "#D10C2229"
    border.color: "#6FE0C8"
    border.width: 1

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 1
        height: 1
        radius: 1
        color: "#66E7FFF7"
    }

    readonly property var tracksInUse: {
        const seen = []
        const labels = []
        for (let i = 0; i < nodes.length; ++i) {
            const track = nodes[i].track
            if (!track || seen.indexOf(track) >= 0)
                continue
            seen.push(track)
            labels.push({ id: track, color: atlas.trackColor(track), label: atlas.trackLabel(track) })
        }
        return labels
    }

    readonly property var layers: [
        { id: "essential", title: "必需" },
        { id: "important", title: "重要" },
        { id: "optional", title: "可选" }
    ]

    Column {
        id: hudColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.leftMargin: 16
        anchors.rightMargin: 16
        spacing: 10

        Row {
            spacing: 14
            Text {
                text: "航路"
                color: "#9AD7C8"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                anchors.verticalCenter: parent.verticalCenter
            }
            Repeater {
                model: [
                    { color: "#7EF0D4", dash: false },
                    { color: "#C9D6A8", dash: true },
                    { color: "#4AD4B2", dash: false, lamp: true }
                ]
                delegate: Row {
                    required property var modelData
                    spacing: 6
                    Rectangle {
                        width: 22
                        height: modelData.dash ? 0 : 3
                        radius: 2
                        color: modelData.color
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !modelData.dash && !modelData.lamp
                    }
                    Rectangle {
                        visible: modelData.lamp === true
                        width: 10
                        height: 10
                        radius: 5
                        color: modelData.color
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Canvas {
                        visible: modelData.dash
                        width: 22
                        height: 8
                        anchors.verticalCenter: parent.verticalCenter
                        onPaint: {
                            const ctx = getContext("2d")
                            ctx.reset()
                            ctx.strokeStyle = modelData.color
                            ctx.lineWidth = 2
                            ctx.setLineDash([4, 3])
                            ctx.beginPath()
                            ctx.moveTo(0, 4)
                            ctx.lineTo(22, 4)
                            ctx.stroke()
                        }
                    }
                }
            }
        }

        Row {
            spacing: 16
            Text {
                text: "能力域"
                color: "#9AD7C8"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                anchors.verticalCenter: parent.verticalCenter
            }
            Repeater {
                model: root.tracksInUse
                delegate: Row {
                    required property var modelData
                    spacing: 5
                    Item {
                        width: 18
                        height: 18
                        TrackGlyph {
                            anchors.fill: parent
                            track: modelData.id
                            ink: modelData.color
                        }
                        HoverHandler { id: glyphHover }
                        ToolTip.visible: glyphHover.hovered
                        ToolTip.text: modelData.label
                        ToolTip.delay: 200
                    }
                }
            }
            Item { width: 12; height: 1 }
            Text {
                text: "分层"
                color: "#9AD7C8"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                anchors.verticalCenter: parent.verticalCenter
            }
            Repeater {
                model: root.layers
                delegate: Rectangle {
                    required property var modelData
                    property bool on: root.layerFilter === modelData.id
                    height: 26
                    width: layerText.implicitWidth + 16
                    radius: 13
                    color: on ? "#2E8F7A" : "#1A3A40"
                    border.color: on ? "#7EF0D4" : "#3D6F70"
                    Text {
                        id: layerText
                        anchors.centerIn: parent
                        text: modelData.title
                        color: "#E8F7F2"
                        font.pixelSize: 12
                    }
                    TapHandler {
                        onTapped: root.layerChosen(modelData.id)
                    }
                }
            }
        }

        Flow {
            visible: root.theory.length > 0
            width: hudColumn.width
            spacing: 8
            Text {
                text: "理论科目"
                color: "#9AD7C8"
                font.pixelSize: 12
                font.weight: Font.DemiBold
                height: 26
                verticalAlignment: Text.AlignVCenter
            }
            Repeater {
                model: root.theory
                delegate: Rectangle {
                    required property var modelData
                    height: 26
                    width: theoryLabel.implicitWidth + 16
                    radius: 13
                    color: theoryHover.hovered ? "#24555C" : "#16343A"
                    border.color: "#4A7A78"
                    Text {
                        id: theoryLabel
                        anchors.centerIn: parent
                        text: modelData.name
                        color: "#E8F7F2"
                        font.pixelSize: 12
                    }
                    HoverHandler { id: theoryHover }
                    TapHandler { onTapped: root.theoryChosen(modelData) }
                }
            }
        }
    }
}
