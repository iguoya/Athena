import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    property int addressBase: 4096
    property int cellBytes: 1
    property var values: [1, 0, 0, 0, 0, 0, 0, 0]
    property int selected: 0
    property string pointerName: ""
    property int pointerIndex: -1
    color: "#1c1917"
    radius: 10
    implicitHeight: 210
    Layout.fillWidth: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 8
        Text {
            text: pointerName.length ? (pointerName + " 里写着 " + hex(addressBase + pointerIndex * cellBytes))
                                     : "点格子看地址"
            color: "#fde68a"
            font.family: "Menlo"
        }
        Row {
            spacing: 8
            Repeater {
                model: root.values
                delegate: Rectangle {
                    required property int index
                    required property var modelData
                    width: 88
                    height: 108
                    radius: 6
                    color: index === root.selected ? "#ea580c" : "#44403c"
                    border.color: index === root.pointerIndex ? "#fde68a" : "transparent"
                    border.width: index === root.pointerIndex ? 2 : 0
                    MouseArea {
                        anchors.fill: parent
                        onClicked: root.selected = index
                    }
                    Column {
                        anchors.centerIn: parent
                        spacing: 4
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: hex(root.addressBase + index * root.cellBytes).slice(-4)
                            color: "#a8a29e"
                            font.family: "Menlo"
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: Number(modelData).toString(16).padStart(2, "0")
                            color: "white"
                            font.family: "Menlo"
                            font.bold: true
                        }
                    }
                }
            }
        }
    }

    function hex(n) {
        return "0x" + Number(n).toString(16)
    }
}
