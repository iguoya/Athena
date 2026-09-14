import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property string kind: "note"
    property string title: ""
    property string body: ""
    Layout.fillWidth: true
    radius: 8
    color: kind === "trap" ? "#f8d7da"
         : kind === "why" ? "#cfe2ff"
         : kind === "use" ? "#d1e7dd"
         : kind === "key" ? "#fff3cd"
         : "#fff3cd"
    border.color: kind === "trap" ? "#dc3545"
                : kind === "why" ? "#0a58ca"
                : kind === "use" ? "#198754"
                : "#b7791f"
    implicitHeight: col.height + 22

    Column {
        id: col
        x: 14
        y: 11
        width: parent.width - 28
        spacing: 4
        Text {
            text: root.title
            font.bold: true
            color: "#1c1917"
        }
        Text {
            width: parent.width
            wrapMode: Text.WordWrap
            text: root.body
            color: "#212529"
        }
    }
}
