import QtQuick

Rectangle {
    id: root
    property var node
    signal opened(string id)

    readonly property bool openable: !!(node && node.openable)
    readonly property color accent: curriculum.difficultyColor(node ? node.difficulty : 0)

    width: node ? node.w : 300
    height: node ? node.h : 140
    radius: 10
    color: openable ? "white" : "#f1f3f5"
    border.width: 2
    border.color: openable ? accent : "#ced4da"
    opacity: openable ? 1 : 0.72

    MouseArea {
        anchors.fill: parent
        enabled: root.openable
        cursorShape: root.openable ? Qt.PointingHandCursor : Qt.ArrowCursor
        hoverEnabled: true
        onClicked: root.opened(root.node.id)
        onEntered: if (root.openable) parent.color = "#e7f1ff"
        onExited: parent.color = root.openable ? "white" : "#f1f3f5"
    }

    Column {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 4
        Text {
            text: node ? node.title : ""
            width: parent.width
            elide: Text.ElideRight
            font.bold: true
            color: "#052c65"
        }
        Text {
            text: node && node.openable
                  ? curriculum.goalLabel(node.mastery_goal)
                  : "规划中"
            color: "#5c636a"
        }
        Rectangle {
            width: parent.width
            height: 4
            radius: 2
            color: "#e9ecef"
            Rectangle {
                width: parent.width * (root.openable ? 0.0 : 0)
                height: parent.height
                radius: 2
                color: root.accent
            }
        }
    }
}
