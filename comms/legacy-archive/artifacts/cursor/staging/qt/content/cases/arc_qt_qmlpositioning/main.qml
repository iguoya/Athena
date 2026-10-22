import QtQuick 2.9
import QtQuick.Window 2.2

Window {
    visible: true
    width: 640
    height: 840
    title: qsTr("Hello World")

    id: root
    Item {
        id: column
        width: 640
        height: 200
        Column {
            anchors.centerIn: parent
            spacing: 10
            RedSquare { width: column.width*1 }
            GreenSquare { width: column.width*0.666 }
            BlueSquare { width: column.width*0.333 }
        }
    }


    Item {
        id: row
        y:column.height
        width: 320
        height: 320
        Row {
            anchors.centerIn: parent
            spacing: 10
            BlueSquare { height: row.height*0.333 }
            GreenSquare { height: row.height*0.666}
            RedSquare { height: row.height }
        }
    }


    Item {
        id: grid
        x: row.width
        y:row.y
        width: 320
        height: 320
        Grid {
            rows: 2
            columns: 2
            anchors.centerIn: parent
            spacing: 10
            RedSquare { }
            RedSquare { }
            RedSquare { }
            RedSquare { }
        }
    }

    Item {
        id:flow
        y:row.y + row.height
        width: 320
        height: 320
        Flow {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 8
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
            RedSquare { }
            BlueSquare { }
            GreenSquare { }
        }
    }
    Item {
        id: repeatGrid
        x:root.width-flow.width
        y:flow.y
        width: 640
        height: 320
        property variant colorArray: ["#00bde3", "#67c111", "#ea7025"]
        Grid{
            rows: 5
            columns: 5
            anchors.fill: parent
            anchors.margins: 10
            spacing: 2
            Repeater {
                model: 25
                Rectangle {
                    width: 56; height: 56
                    property int colorIndex: Math.floor(Math.random()*3)
                    color: repeatGrid.colorArray[colorIndex]
                    border.color: Qt.lighter(color)
                    Text {
                        anchors.centerIn: parent
                        color: "#f0f0f0"
                        text: "Cell " + index
                    }
                }
            }
        }
    }

}
