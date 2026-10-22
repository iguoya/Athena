import QtQuick 2.12
import QtQuick.Window 2.12
import QtQuick.Controls 2.5


Window {
    visible: true
    Button {
        text: "hello"
        anchors.centerIn: parent
        MouseArea {
            anchors.fill: parent
            onClicked: {
                Qt.quit()
            }
        }
    }

    Hello {
        anchors.centerIn: bottom
        //        anchors.fill: parent

    }
}
