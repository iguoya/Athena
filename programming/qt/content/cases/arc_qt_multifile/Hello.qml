import QtQuick 2.0

Rectangle {
    width: 100
    height: 30
    Text {
        text: "郭雅"
        anchors.centerIn: parent
    }
    MouseArea {
        anchors.fill: parent
        onClicked: {
            Qt.quit()
        }
    }
}
