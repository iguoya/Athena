import QtQuick 2.12
import QtQuick.Controls 2.5

Page {
    width: 600
    height: 400

    header: Label {
        text: qsTr("Page 2")
        font.pixelSize: Qt.application.font.pixelSize * 2
        padding: 10
    }

    Label {
        text: qsTr("You are on Page 2.")
        anchors.verticalCenterOffset: -127
        anchors.horizontalCenterOffset: -38
        anchors.centerIn: parent
    }

    TextArea {
        id: textArea
        x: 136
        y: 92
        width: 350
        height: 185
        placeholderText: qsTr("Text Area")
    }
}
