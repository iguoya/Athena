import QtQuick 2.9
import QtQuick.Window 2.2

Window {

    visible: true
    width: 960
    height: 540
    title: qsTr("基本的QML语法")
    // The root element is the Rectangle
    Rectangle {
        // name this element root
        id: root

        // properties: <name>: <value>
        width: (parent.width)/2 ; height: (parent.height)/2

        // color property
        color: "blue"

        // Declare a nested element (child of root)
        Image {
            id: triangle

            // reference the parent
            x: (parent.width - width)/2; y: (parent.height-height)/2

            source: 'assets/triangle_blue.png'
        }

        // Another child of root
        Text {
            // un-named element

            // reference element by id
            y: triangle.y - 40

            // reference root element
            width: root.width

            color: 'white'
            horizontalAlignment: Text.AlignHCenter
            text: '三角形'
        }
    }
//    Rectangle {

//        x:0
//        y:
//        width: parent.width/2
//        height: parent.height/2
//        color:"orange"


        Text {
            // (1) identifier
            id: thisLabel

            // (2) set x- and y-position
            x: parent.width/2-100; y: parent.height/2

            // (3) bind height to 2 * width
//            height: parent.height/4

            // (4) custom property
//            property int times: 24

            // (5) property alias
            property alias anotherTimes: thisLabel.times
            property int times: 0
            // (6) set text appended by value
            text: "点击空格次数    ：    " + times +"    次 ！～～～～～"

            // (7) font is a grouped property
            font.family: "Ubuntu"
            font.pixelSize: 24

            // (8) KeyNavigation is an attached property
            KeyNavigation.tab: otherLabel

            // (9) signal handler for property changes
            onHeightChanged:{ console.log('height:', height);
            }

            // focus is need to receive key events

             focus: true

            // change color based on focus value


            color: times % 2 ?"red":"purple"
            onTextChanged: console.log("text changed to:", text)
            Keys.onSpacePressed: {
//                increment()
                times = times + 1
//                if(focus == true) {
//                    focus = false
//                } else {
//                    focus = true
//                }

            }

            // clear the text on escape
            Keys.onEscapePressed: {
//                thisLabel.text = ''
                times = 0;
            }

            // (3) a JS function
//            function increment() {
//                times = times + 1
//            }

        }
        Text {
            // (1) identifier
            id: otherLabel
            x: parent.width/2-100; y:  parent.height/2+thisLabel.height
            text: "输入ESC取消次数"
            // (6) font is a grouped property
            font.family: "Ubuntu"
            font.pixelSize: 24

            // (7) Keys is a attached property
            KeyNavigation.tab: thisLabel
            color: thisLabel.times % 2 ? "blue":"green"

        }
        //    }


}
