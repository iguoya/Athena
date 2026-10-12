import QtQuick
import "../components" as C

Item {
    id: root
    implicitWidth: curriculum.topicGraphWidth
    implicitHeight: curriculum.topicGraphHeight
    width: Math.max(parent ? parent.width : 0, curriculum.topicGraphWidth)
    height: curriculum.topicGraphHeight

    Canvas {
        id: edges
        anchors.fill: parent
        z: 0
        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            const list = curriculum.topicEdges
            for (let i = 0; i < list.length; ++i) {
                const e = list[i]
                const mid = (e.y0 + e.y1) / 2
                ctx.beginPath()
                ctx.strokeStyle = "#bcc4ce"
                ctx.lineWidth = 1.6
                ctx.moveTo(e.x0, e.y0)
                ctx.bezierCurveTo(e.x0, mid, e.x1, mid, e.x1, e.y1 - 6)
                ctx.stroke()
                ctx.beginPath()
                ctx.fillStyle = "#bcc4ce"
                ctx.moveTo(e.x1, e.y1)
                ctx.lineTo(e.x1 - 4.5, e.y1 - 7)
                ctx.lineTo(e.x1 + 4.5, e.y1 - 7)
                ctx.closePath()
                ctx.fill()
            }
        }
        Component.onCompleted: requestPaint()
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }

    Repeater {
        model: curriculum.topicNodes
        delegate: C.TopicNode {
            required property var modelData
            z: 1
            node: modelData
            x: modelData.x
            y: modelData.y
            onOpened: function (id) { curriculum.select(id) }
        }
    }

    Connections {
        target: curriculum
        function onSelectionChanged() { edges.requestPaint() }
    }
}
