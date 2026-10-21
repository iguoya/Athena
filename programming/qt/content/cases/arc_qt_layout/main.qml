import QtQuick 2.12
import QtQuick.Window 2.12

//Window {
//    width: 640
//    height: 480
//    visible: true
//    title: qsTr("Hello World")
//}

Window {
    width: 200
    height: 200
    visible: true
    title: qsTr("Hello World")
    Rectangle {
        x: 50
        y: 50
        width: 100
        height: 100
        color: "green"
    }

    Rectangle {
        x: 100
        y: 100
        width: 50
        height: 50
        color: "yellow"
    }
}
