import QtQuick
import QtQuick.Shapes

// 当前点的邻域：左进右出。点胶囊进专页，实线是门槛，虚线是来路。
Item {
    id: root
    required property var inbound
    required property var outbound
    required property string centerTitle
    required property color accent
    signal nodeOpened(string nodeId)

    readonly property int pillW: 168
    readonly property int pillH: 36
    readonly property real cx: width / 2
    readonly property real cy: height / 2

    function slotY(count, index) {
        if (count <= 1)
            return height / 2
        const span = Math.min(height - 64, Math.max(56, (count - 1) * 52))
        const start = (height - span) / 2
        return start + index * (span / Math.max(1, count - 1))
    }

    Repeater {
        model: root.inbound
        delegate: Shape {
            required property var modelData
            required property int index
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            antialiasing: true
            ShapePath {
                strokeColor: modelData.strong ? "#7EF0D4" : "#C9D6A8"
                strokeWidth: modelData.strong ? 2.4 : 1.6
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                dashPattern: modelData.strong ? [] : [6, 7]
                PathMove {
                    x: 24 + root.pillW
                    y: root.slotY(root.inbound.length, index)
                }
                PathCubic {
                    control1X: root.width * 0.38
                    control1Y: root.slotY(root.inbound.length, index)
                    control2X: root.width * 0.42
                    control2Y: root.cy
                    x: root.cx - 46
                    y: root.cy
                }
            }
        }
    }

    Repeater {
        model: root.outbound
        delegate: Shape {
            required property var modelData
            required property int index
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            antialiasing: true
            ShapePath {
                strokeColor: modelData.strong ? "#7EF0D4" : "#C9D6A8"
                strokeWidth: modelData.strong ? 2.4 : 1.6
                fillColor: "transparent"
                capStyle: ShapePath.RoundCap
                dashPattern: modelData.strong ? [] : [6, 7]
                PathMove { x: root.cx + 46; y: root.cy }
                PathCubic {
                    control1X: root.width * 0.58
                    control1Y: root.cy
                    control2X: root.width * 0.62
                    control2Y: root.slotY(root.outbound.length, index)
                    x: root.width - 24 - root.pillW
                    y: root.slotY(root.outbound.length, index)
                }
            }
        }
    }

    Repeater {
        model: root.inbound
        delegate: Rectangle {
            required property var modelData
            required property int index
            width: root.pillW
            height: root.pillH
            radius: 12
            x: 24
            y: root.slotY(root.inbound.length, index) - root.pillH / 2
            color: inHover.hovered ? "#3A2E8F7A" : "#2215262C"
            border.color: modelData.strong ? "#7EF0D4" : "#8AA8A2"
            MapText {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                text: modelData.title || ""
                color: "#E8F7F2"
                font.pixelSize: 13
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            HoverHandler { id: inHover }
            TapHandler { onTapped: root.nodeOpened(modelData.id) }
        }
    }

    Repeater {
        model: root.outbound
        delegate: Rectangle {
            required property var modelData
            required property int index
            width: root.pillW
            height: root.pillH
            radius: 12
            x: root.width - 24 - root.pillW
            y: root.slotY(root.outbound.length, index) - root.pillH / 2
            color: outHover.hovered ? "#3A2E8F7A" : "#2215262C"
            border.color: modelData.strong ? "#7EF0D4" : "#8AA8A2"
            MapText {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 8
                text: modelData.title || ""
                color: "#E8F7F2"
                font.pixelSize: 13
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            HoverHandler { id: outHover }
            TapHandler { onTapped: root.nodeOpened(modelData.id) }
        }
    }

    Rectangle {
        width: 96
        height: 96
        radius: 48
        anchors.centerIn: parent
        color: root.accent
        border.color: "#E7FFF7"
        border.width: 2
        MapText {
            anchors.fill: parent
            anchors.margins: 10
            text: root.centerTitle
            color: "#FFFFFF"
            font.pixelSize: 13
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            maximumLineCount: 3
            elide: Text.ElideRight
        }
    }

    Rectangle {
        visible: root.inbound.length === 0
        width: 18
        height: 18
        radius: 9
        x: 36
        anchors.verticalCenter: parent.verticalCenter
        color: "#4AD4B2"
        SequentialAnimation on opacity {
            running: visible
            loops: Animation.Infinite
            NumberAnimation { from: 0.4; to: 1; duration: 900 }
            NumberAnimation { from: 1; to: 0.4; duration: 900 }
        }
    }
}
