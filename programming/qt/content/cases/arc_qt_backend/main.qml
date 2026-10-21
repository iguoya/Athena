import QtQuick 2.12
import QtQuick.Window 2.12
import QtQuick.Controls 2.12
import io.qt.examples.backend 1.0

ApplicationWindow {
    width: 640
    height: 480
    visible: true
    title: qsTr("Hello World")

    BackEnd {
        id: backend
        onUserNameChanged: console.log(backend.userName)
    }

    Column {
        anchors.centerIn: parent
        TextField {
            onTextChanged: backend.userName = text
        }

        Label {
    //        anchors.centerIn: parent
            text: backend.userName

            width:200
            font.pointSize: 20

            background: Rectangle {
                color: "lightgrey"
            }
        }
    }


}
