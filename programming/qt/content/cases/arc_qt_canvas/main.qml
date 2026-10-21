import QtQuick 2.12
import QtQuick.Window 2.12

Window {
    width: 640
    height: 480
    visible: true
    title: qsTr("Hello World")

    Canvas {

           anchors.fill: parent
           anchors.centerIn: parent

           onPaint: {

               var ctx = getContext("2d");
               ctx.fillStyle = "lightslategray"

               ctx.beginPath();
               ctx.fillRect(10, 10, 80, 50);

               ctx.beginPath();
               ctx.fillRect(120, 10, 70, 70);

               ctx.beginPath();
               ctx.ellipse(230, 10, 90, 70);
               ctx.fill();

               ctx.beginPath();
               ctx.ellipse(10, 110, 70, 70);
               ctx.fill();

               ctx.beginPath();
               ctx.roundedRect(120, 110, 70, 70, 10, 10);
               ctx.fill();

               ctx.beginPath();
               ctx.moveTo(230, 110);
               ctx.arc(230, 110, 70, 0, Math.PI * 0.5, false);
               ctx.fill();

           }
       }
}
