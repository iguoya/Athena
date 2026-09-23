import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property string goal: "master"
    property string label: ""
    property string note: ""
    Layout.fillWidth: true
    radius: 8
    color: goal === "master" ? "#e7f1ff"
         : goal === "required" ? "#e6f4f1"
         : "#f1f3f5"
    border.color: goal === "master" ? "#0a58ca"
                : goal === "required" ? "#0f766e"
                : "#6c757d"
    implicitHeight: col.height + 20

    Column {
        id: col
        x: 12
        y: 10
        width: parent.width - 24
        spacing: 6
        Row {
            spacing: 8
            Rectangle {
                width: badge.implicitWidth + 16
                height: badge.implicitHeight + 10
                radius: 4
                color: root.border.color
                Text {
                    id: badge
                    anchors.centerIn: parent
                    text: root.label
                    color: "white"
                    font.bold: true
                }
            }
        }
        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            text: root.note
            color: "#212529"
        }
    }
}
