import QtQuick 2.12
import QtQuick.Controls 2.5
import QtQuick.Controls.Styles.Desktop 1.0

Page {
    width: 600
    height: 400
    property alias button: button

    header: Label {
        text: qsTr("Page 1")
        font.pixelSize: Qt.application.font.pixelSize * 2
        padding: 10
    }

    Label {
        text: qsTr("You are on Page 1.")
        anchors.verticalCenterOffset: 75
        anchors.horizontalCenterOffset: -20
        anchors.centerIn: parent
    }

    Button {
        id: button
        x: 237
        y: 149
        text: qsTr("计算")
    }

    Text {
        id: text1
        x: 174
        y: 104
        width: 143
        height: 39
        font.pixelSize: 12
    }

    TextInput {
        id: textInput
        x: 174
        y: 45
        width: 276
        height: 20
        font.pixelSize: 12
    }

    Label {
        id: label
        x: 46
        y: 43
        width: 103
        height: 28
        text: qsTr("输入半径")
    }

    Label {
        id: label1
        x: 46
        y: 103
        width: 103
        height: 28
        text: qsTr("面积结果")
    }
}
