import QtQuick 2.12
import QtQuick.Window 2.12

Window {
    visible: true
    width: 800
    height: 600

    Rectangle {
        anchors.fill: parent
        anchors.margins: 20
        color: "lightyellow"

        Text {
            id: text
            anchors.centerIn: parent
            text: qsTr("Hello world! 郭雅")
            font.pointSize: 30
        }

        Rectangle {
            id: rect1
            width: 50
            height: 50
//            anchors.bottom: text.baseline
            anchors.top: text.bottom
            color: "lightgreen"
        }

        Rectangle {
            width: 100
            height: 100
//            anchors.horizontalCenter: rect1.horizontalCenter
//            anchors.horizontalCenterOffset: 25
            anchors.left: rect1.right
            anchors.bottom: rect1.bottom
//            anchors.bottomMargin: 10
            color: "gold"
        }
    }
}
