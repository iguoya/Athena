import QtQuick 2.12
import QtQuick.Window 2.12
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.11

Window {
    width: 640
    height: 480
    visible: true
    title: qsTr("Hello World")

    GridLayout {
        anchors.fill: parent
        rows: 3
        columns: 4

        Button {
            id: button
            text: qsTr("Button")
        }

        Button {
            id: button1
            text: qsTr("Button")
        }

        Button {
            id: button2
            text: qsTr("Button")
        }

        Button {
            id: button3
            text: qsTr("Button")
        }

        Button {
            id: button4
            text: qsTr("Button")
        }

        Button {
            id: button5
            text: qsTr("Button")
        }

        Button {
            id: button6
            text: qsTr("Button")
        }

        Button {
            id: button7
            text: qsTr("Button")
        }

        Button {
            id: button8
            text: qsTr("Button")
        }

        Button {
            id: button9
            text: qsTr("Button")
        }

        Button {
            id: button10
            text: qsTr("Button")
        }

        Button {
            id: button11
            text: qsTr("Button")
        }
    }


}
