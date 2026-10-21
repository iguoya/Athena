import QtQuick 2.12
import QtQuick.Controls 2.5
import qt.tiger.circle 1.0

Page {
    width: 600
    height: 400
    property alias button: button

    title: qsTr("Page 1")
    Circle {
        id:circle
        onAreaChanged:text1.text = circle.area
    }

    Label {
        width: 137
        height: 52
        text: qsTr("输入半径")
        anchors.verticalCenterOffset: -78
        anchors.horizontalCenterOffset: -150
        anchors.centerIn: parent
    }

    TextEdit {
        id: textEdit
        x: 265
        y: 91
        width: 175
        height: 42
        font.pixelSize: 12
//        onTextChanged: circle.
    }

    Label {
        id: label
        x: 91
        y: 240
        width: 117
        height: 51
        text: qsTr("面积结果")
    }

    Text {
        id: text1
        x: 265
        y: 236
        width: 203
        height: 55
        text: qsTr("Text")
        font.pixelSize: 12
    }

    Button {
        id: button
        x: 226
        y: 325
        text: qsTr("Button")
        onClicked: {
            circle.setArea(textEdit.text)
//            text1.text = circle.area
        }

    }
}
