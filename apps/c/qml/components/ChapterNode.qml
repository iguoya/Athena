import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property var node
    signal opened(string id)

    readonly property bool planned: !!(node && node.planned)
    readonly property color accent: curriculum.difficultyColor(node ? node.difficulty : 0)

    width: node ? node.w : 400
    height: node ? node.h : 420
    radius: 16
    color: planned ? "#f1f3f5" : "white"
    border.width: node && node.on_main_path ? 3 : 2
    border.color: planned ? "#ced4da" : accent
    opacity: planned ? 0.88 : 1

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        onClicked: root.opened(root.node.id)
        onEntered: parent.color = root.planned ? "#e9ecef" : "#e7f1ff"
        onExited: parent.color = root.planned ? "#f1f3f5" : "white"
    }

    Column {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 8

        Text {
            text: node ? node.title : ""
            width: parent.width
            wrapMode: Text.WordWrap
            font.bold: true
            color: "#052c65"
        }
        Row {
            spacing: 6
            Rectangle {
                visible: !!(node && node.on_main_path)
                width: mainLabel.implicitWidth + 16
                height: mainLabel.implicitHeight + 8
                radius: 10
                color: "#1d4ed8"
                Text {
                    id: mainLabel
                    anchors.centerIn: parent
                    text: "学习主干"
                    color: "white"
                    font.bold: true
                }
            }
            Rectangle {
                visible: root.planned
                width: planLabel.implicitWidth + 16
                height: planLabel.implicitHeight + 8
                radius: 10
                color: "#6c757d"
                Text {
                    id: planLabel
                    anchors.centerIn: parent
                    text: "规划中"
                    color: "white"
                    font.bold: true
                }
            }
        }
        Text {
            text: node ? (node.description || "") : ""
            width: parent.width
            wrapMode: Text.WordWrap
            maximumLineCount: 3
            elide: Text.ElideRight
            color: "#5c636a"
        }
        Row {
            spacing: 6
            Rectangle {
                width: dlabel.implicitWidth + 16
                height: dlabel.implicitHeight + 8
                radius: 11
                color: root.accent
                Text {
                    id: dlabel
                    anchors.centerIn: parent
                    text: node && node.difficulty > 0
                          ? ("难度 " + node.difficulty + "/5")
                          : "难度 未评"
                    color: "white"
                    font.bold: true
                }
            }
            Rectangle {
                width: mlabel.implicitWidth + 16
                height: mlabel.implicitHeight + 8
                radius: 11
                color: "#e9ecef"
                Text {
                    id: mlabel
                    anchors.centerIn: parent
                    text: node
                          ? ("已写 " + node.open_count + "/" + node.topic_count)
                          : ""
                    color: "#343a40"
                    font.bold: true
                }
            }
        }
        Rectangle {
            width: parent.width
            height: 6
            radius: 3
            color: "#e9ecef"
            Rectangle {
                width: parent.width * (node && node.topic_count > 0
                                       ? node.open_count / node.topic_count
                                       : 0)
                height: parent.height
                radius: 3
                color: root.accent
            }
        }
        Repeater {
            model: node && node.points ? node.points : []
            delegate: Text {
                required property var modelData
                width: parent.width
                text: (modelData.openable ? "●  " : "○  ") + modelData.title
                color: modelData.openable ? "#212529" : "#868e96"
                elide: Text.ElideRight
            }
        }
    }
}
