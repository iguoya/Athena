import QtQuick

Item {
    id: root
    required property var node
    property bool selected: false
    property bool hovered: false
    property bool lit: true
    property int inbound: 0
    property int outbound: 0
    signal chosen(string nodeId)
    signal opened(string nodeId)
    signal entered()
    signal exited()

    width: node.w
    height: node.h
    opacity: lit ? 1 : 0.22
    Behavior on opacity { NumberAnimation { duration: 180 } }

    property color accent: atlas.trackColor(node.track)
    property bool courseNode: Boolean(node.verify)

    Rectangle {
        anchors.centerIn: card
        width: card.width + 36
        height: card.height + 36
        radius: 26
        color: root.accent
        opacity: root.selected ? 0.42 : (root.hovered ? 0.22 : (Boolean(root.node.entry) ? 0.12 : 0.06))
        Behavior on opacity { NumberAnimation { duration: 200 } }
    }

    Rectangle {
        visible: Boolean(root.node.entry)
        anchors.horizontalCenter: card.horizontalCenter
        anchors.top: card.top
        anchors.topMargin: -11
        width: 18
        height: 18
        radius: 9
        color: "#4AD4B2"
        SequentialAnimation on opacity {
            running: visible && root.lit
            loops: Animation.Infinite
            NumberAnimation { from: 0.35; to: 1; duration: 900 }
            NumberAnimation { from: 1; to: 0.35; duration: 900 }
        }
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: 16
        antialiasing: true
        color: root.selected ? "#FFF6E4" : (root.hovered ? "#F3FBFF" : "#F7FAF8")
        border.color: root.selected ? "#E08A4A" : root.accent
        border.width: root.selected ? 2 : 1

        Rectangle {
            width: 8
            height: parent.height
            radius: 16
            color: root.accent
        }

        Column {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 14
            anchors.topMargin: 14
            anchors.bottomMargin: 12
            spacing: 10

            Row {
                spacing: 8
                TrackGlyph {
                    track: root.node.track || ""
                    ink: root.accent
                    width: 22
                    height: 22
                    anchors.verticalCenter: parent.verticalCenter
                }
                PriorityMeter {
                    priority: root.node.priority || ""
                    lamp: 9
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            MapText {
                width: parent.width
                text: root.node.title
                color: "#132B32"
                font.pixelSize: 18
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                lineHeight: 1.25
                lineHeightMode: Text.ProportionalHeight
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            Item { width: 1; height: 4 }

            Row {
                spacing: 14
                Repeater {
                    model: [
                        { n: root.inbound, mark: "◀", tone: "#2E6F78" },
                        { n: root.outbound, mark: "▶", tone: "#4969A8" }
                    ]
                    delegate: Column {
                        required property var modelData
                        spacing: 2
                        MapText {
                            text: modelData.mark + " " + modelData.n
                            color: modelData.tone
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                        }
                        Rectangle {
                            width: Math.max(8, modelData.n * 10)
                            height: 4
                            radius: 2
                            color: modelData.tone
                            opacity: 0.7
                        }
                    }
                }
            }

            MapText {
                visible: root.selected
                text: "双击进入 →"
                color: "#C45C2A"
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }
        }
    }

    HoverHandler {
        onHoveredChanged: {
            if (hovered)
                root.entered()
            else
                root.exited()
        }
    }
    TapHandler {
        onTapped: root.chosen(root.node.id)
        onDoubleTapped: root.opened(root.node.id)
    }
}
