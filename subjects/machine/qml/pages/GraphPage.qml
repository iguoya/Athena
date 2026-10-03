import QtQuick
import QtQuick.Controls
import "../components" as C

Flickable {
    id: root
    clip: true
    contentWidth: Math.max(width, curriculum.graphWidth + 40)
    contentHeight: Math.max(height, curriculum.graphHeight + 48)
    ScrollBar.vertical: ScrollBar {}
    ScrollBar.horizontal: ScrollBar {}

    Item {
        id: board
        x: Math.max(20, Math.floor((root.width - curriculum.graphWidth) / 2))
        y: 12
        width: curriculum.graphWidth
        height: curriculum.graphHeight

        Canvas {
            id: edges
            anchors.fill: parent
            z: 0
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                const list = curriculum.graphEdges
                for (let i = 0; i < list.length; ++i) {
                    const e = list[i]
                    const x0 = e.x0
                    const y0 = e.y0
                    const x1 = e.x1
                    const y1 = e.y1
                    const mid = (y0 + y1) / 2
                    ctx.beginPath()
                    ctx.strokeStyle = "#9aa4af"
                    ctx.lineWidth = 2
                    ctx.moveTo(x0, y0)
                    ctx.bezierCurveTo(x0, mid, x1, mid, x1, y1 - 7)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.fillStyle = "#9aa4af"
                    ctx.moveTo(x1, y1)
                    ctx.lineTo(x1 - 5.5, y1 - 9)
                    ctx.lineTo(x1 + 5.5, y1 - 9)
                    ctx.closePath()
                    ctx.fill()
                }
            }
            Component.onCompleted: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
        }

        Repeater {
            model: curriculum.graphNodes
            delegate: C.ChapterNode {
                required property var modelData
                z: 1
                node: modelData
                x: modelData.x
                y: modelData.y
                onOpened: function (id) { curriculum.openChapter(id) }
            }
        }

        Connections {
            target: curriculum
            function onCatalogChanged() { edges.requestPaint() }
        }
    }
}
