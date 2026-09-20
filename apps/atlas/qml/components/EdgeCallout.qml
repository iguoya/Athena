import QtQuick
import QtQuick.Shapes

Rectangle {
    id: root
    required property var edge
    signal closed()

    visible: Boolean(edge)
    width: Math.min(460, parent.width - 48)
    height: calloutColumn.height + 28
    radius: 18
    color: "#F2FAF7"
    border.color: "#E08A4A"
    border.width: 2

    readonly property bool strong: edge && edge.strong

    Column {
        id: calloutColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 16
        spacing: 12

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 10
            Rectangle {
                width: 148
                height: 40
                radius: 12
                color: "#132B32"
                MapText {
                    anchors.fill: parent
                    anchors.margins: 8
                    text: root.edge ? atlas.nodeTitle(root.edge.from) : ""
                    color: "#E8F7F2"
                    font.pixelSize: 13
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
            Shape {
                width: 72
                height: 40
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeColor: root.strong ? "#128C7A" : "#8A9A4A"
                    strokeWidth: root.strong ? 3.2 : 1.8
                    fillColor: "transparent"
                    capStyle: ShapePath.RoundCap
                    dashPattern: root.strong ? [] : [6, 6]
                    PathMove { x: 4; y: 20 }
                    PathLine { x: 54; y: 20 }
                }
                ShapePath {
                    strokeWidth: 0
                    fillColor: root.strong ? "#128C7A" : "#8A9A4A"
                    PathMove { x: 66; y: 20 }
                    PathLine { x: 52; y: 12 }
                    PathLine { x: 52; y: 28 }
                    PathLine { x: 66; y: 20 }
                }
            }
            Rectangle {
                width: 148
                height: 40
                radius: 12
                color: "#132B32"
                MapText {
                    anchors.fill: parent
                    anchors.margins: 8
                    text: root.edge ? atlas.nodeTitle(root.edge.to) : ""
                    color: "#E8F7F2"
                    font.pixelSize: 13
                    elide: Text.ElideRight
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Rectangle {
            width: parent.width
            height: 28
            radius: 14
            color: root.strong ? "#128C7A" : "#5C6B75"
            MapText {
                anchors.centerIn: parent
                text: root.strong ? "门槛  ·  过不去就不能往下" : "来路  ·  不是门槛"
                color: "#FFFFFF"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
        }

        MapText {
            width: parent.width
            text: root.edge ? (root.edge.rationale || "") : ""
            color: "#40545B"
            font.pixelSize: 15
            wrapMode: Text.WordWrap
            lineHeight: 1.3
            lineHeightMode: Text.ProportionalHeight
        }
    }
}
