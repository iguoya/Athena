import QtQuick 2.12
import QtQuick.Controls 2.5

Page {
    width: 1920
    height: 1080

    title: qsTr("Page 1")

    Label {
        text: qsTr("You are on Page 1.")
        anchors.centerIn: parent
    }
}
