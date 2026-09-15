import QtQuick
import QtQuick.Controls

Item {
    id: root
    required property var node
    property bool selected: false
    signal chosen(string nodeId)
    width: node.w
    height: node.h

    property color accent: atlas.trackColor(node.track)

    Rectangle {
        id: card
        anchors.fill: parent
        radius: 14
        color: root.selected ? "#FFF7E8" : (mouse.containsMouse ? "#F4FAF7" : "#FFFFFF")
        border.color: root.selected ? "#B84B47" : root.accent
        border.width: root.selected ? 3 : 1
        layer.enabled: true

        Column {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 9
            Row {
                width: parent.width
                spacing: 8
                Rectangle { width: 10; height: 10; radius: 5; color: root.accent; anchors.verticalCenter: parent.verticalCenter }
                Text {
                    width: parent.width - 18
                    text: atlas.priorityLabel(root.node.priority_tier) + " · " + atlas.volatilityLabel(root.node.volatility)
                    color: atlas.priorityColor(root.node.priority_tier)
                    font.pixelSize: 13
                    elide: Text.ElideRight
                }
            }
            Text {
                width: parent.width
                text: root.node.title
                color: "#182F38"
                font.pixelSize: 20
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }
            Text {
                width: parent.width
                text: (root.node.kit && root.node.kit.tooling) ? root.node.kit.tooling : root.node.engineering_role
                color: "#50636A"
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                maximumLineCount: 3
                elide: Text.ElideRight
            }
        }
    }
    HoverHandler { id: mouse }
    TapHandler { onTapped: root.chosen(root.node.id) }
}
