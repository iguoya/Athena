import QtQuick 2.12
import QtQuick.Controls 2.5

ApplicationWindow {
    width: 640
    height: 480
    visible: true
    title: qsTr("Scroll")

    Button {
//        anchors.fill: parent
        text: "郭雅"
//        MouseArea.onClicked: {
//            Qt.quit()
//        }

//        ListView {
//            id: listView
//            width: parent.width
//            model: 20
//            delegate: ItemDelegate {
//                text: "Item " + (index + 1)
        //                width: listView.width
        //            }
        //        }
    }

    Button {
        id: button
        x: 181
        y: 88
        text: qsTr("Button")
    }

    Button {
        id: button1
        x: 181
        y: 216
        text: qsTr("Button")
    }

    Button {
        id: button2
        x: 360
        y: 88
        text: qsTr("Button")
    }

    Button {
        id: button3
        x: 360
        y: 216
        text: qsTr("Button")
    }
}
