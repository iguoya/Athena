import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property string leftTitle: ""
    property string leftBody: ""
    property string rightTitle: ""
    property string rightBody: ""
    color: "transparent"
    implicitHeight: row.height
    Layout.fillWidth: true

    RowLayout {
        id: row
        width: parent.width
        spacing: 12
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: leftCol.height + 24
            color: "#ecfdf5"
            radius: 8
            Column {
                id: leftCol
                x: 14
                y: 12
                width: parent.width - 28
                spacing: 6
                Text { text: root.leftTitle; font.bold: true; color: "#065f46" }
                Text { text: root.leftBody; wrapMode: Text.WordWrap; width: parent.width; color: "#1c1917" }
            }
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: rightCol.height + 24
            color: "#fff1f2"
            radius: 8
            Column {
                id: rightCol
                x: 14
                y: 12
                width: parent.width - 28
                spacing: 6
                Text { text: root.rightTitle; font.bold: true; color: "#9f1239" }
                Text { text: root.rightBody; wrapMode: Text.WordWrap; width: parent.width; color: "#1c1917" }
            }
        }
    }
}
