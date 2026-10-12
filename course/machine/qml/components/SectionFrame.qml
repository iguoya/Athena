import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property string title: ""
    default property alias content: bodyColumn.data
    color: "white"
    radius: 8
    border.color: "#dee2e6"
    implicitHeight: inner.implicitHeight + 28
    Layout.fillWidth: true

    ColumnLayout {
        id: inner
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 14
        spacing: 10
        Text {
            text: root.title
            font.pointSize: 24
            font.bold: true
            color: "#052c65"
        }
        ColumnLayout {
            id: bodyColumn
            Layout.fillWidth: true
            spacing: 10
        }
    }
}
