import QtQuick 2.12
import QtQuick.Window 2.12

import QtQuick.Layouts 1.12

Window {
    visible: true
    width: 400
    height: 300

    StackLayout {
        id: layout
        anchors.fill: parent
        currentIndex: 1

        Rectangle {
            color: 'teal'
            implicitWidth: 200
            implicitHeight: 200
        }

        Rectangle {
            color: 'plum'
            implicitWidth: 300
            implicitHeight: 200
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            console.log(layout.count)
            layout.currentIndex == 1 ?
                        layout.currentIndex = 0
                      : layout.currentIndex = 1
        }
    }
}
