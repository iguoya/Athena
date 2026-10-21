import QtQuick 2.12
import QtQuick.Controls 2.5

Page {
    width: 600
    height: 400
    property alias button: button
     property alias button: button

    header: Label {
        text: qsTr("Page 1")
        font.pixelSize: Qt.application.font.pixelSize * 2
        padding: 10
    }

    Label {
        text: qsTr("You are on Page 1.")
        anchors.verticalCenterOffset: -110
        anchors.horizontalCenterOffset: -26
        anchors.centerIn: parent
    }

    Button {
        id: button
        x: 264
        y: 135
        text: qsTr("Button")
    }
}
