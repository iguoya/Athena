import QtQuick
import QtQuick.Controls

Flickable {
    id: root
    required property var nodes
    required property var edges
    required property int canvasWidth
    required property int canvasHeight
    required property string selectedNodeId
    signal nodeChosen(string nodeId)
    signal blankChosen()

    clip: true
    contentWidth: width
    contentHeight: height
    boundsBehavior: Flickable.StopAtBounds

    property real zoom: 0.72
    property real minZoom: 0.42
    property real maxZoom: 1.34

    function resetView() {
        zoom = Math.min(0.86, Math.max(minZoom, (Math.min(width / canvasWidth, height / canvasHeight) * 0.88)))
        board.x = Math.round((width - canvasWidth * zoom) / 2)
        board.y = Math.max(18, Math.round((height - canvasHeight * zoom) / 2))
    }

    Component.onCompleted: resetView()
    onWidthChanged: resetView()
    onHeightChanged: resetView()
    onCanvasWidthChanged: resetView()
    onCanvasHeightChanged: resetView()

    Item {
        id: board
        width: root.canvasWidth
        height: root.canvasHeight
        scale: root.zoom
        transformOrigin: Item.TopLeft

        Rectangle {
            anchors.fill: parent
            radius: 18
            color: "#FCFBF6"
            border.color: "#D7DDD5"
            border.width: 1
        }

        Canvas {
            id: edgeLayer
            anchors.fill: parent
            z: 1
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                const nodeById = {}
                for (let i = 0; i < root.nodes.length; ++i) nodeById[root.nodes[i].id] = root.nodes[i]
                for (let i = 0; i < root.edges.length; ++i) {
                    const edge = root.edges[i]
                    const from = nodeById[edge.from]
                    const to = nodeById[edge.to]
                    if (!from || !to) continue
                    const active = root.selectedNodeId.length > 0
                        && (edge.from === root.selectedNodeId || edge.to === root.selectedNodeId)
                    const strong = edge.relation === "requires"
                    const color = active ? "#B84B47" : (strong ? "#758A88" : "#B4C1BD")
                    ctx.beginPath()
                    ctx.strokeStyle = color
                    ctx.lineWidth = active ? 3.3 : (strong ? 2.3 : 1.7)
                    ctx.setLineDash(strong ? [] : [8, 7])
                    const x0 = from.x + from.w / 2
                    const y0 = from.y + from.h
                    const x1 = to.x + to.w / 2
                    const y1 = to.y
                    const mid = (y0 + y1) / 2
                    ctx.moveTo(x0, y0)
                    ctx.bezierCurveTo(x0, mid, x1, mid, x1, y1 - 9)
                    ctx.stroke()
                    ctx.setLineDash([])
                    ctx.beginPath()
                    ctx.fillStyle = color
                    ctx.moveTo(x1, y1)
                    ctx.lineTo(x1 - 6, y1 - 11)
                    ctx.lineTo(x1 + 6, y1 - 11)
                    ctx.closePath()
                    ctx.fill()
                }
            }
            Component.onCompleted: requestPaint()
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            Connections {
                target: root
                function onNodesChanged() { edgeLayer.requestPaint() }
                function onEdgesChanged() { edgeLayer.requestPaint() }
                function onSelectedNodeIdChanged() { edgeLayer.requestPaint() }
            }
        }

        Repeater {
            model: root.nodes
            delegate: RouteNode {
                required property var modelData
                z: 2
                node: modelData
                selected: root.selectedNodeId === modelData.id
                x: modelData.x
                y: modelData.y
                onChosen: function(id) { root.nodeChosen(id) }
            }
        }
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: function(eventPoint) {
            const position = eventPoint.position
            const onBoard = position.x >= board.x && position.x <= board.x + board.width * root.zoom
                && position.y >= board.y && position.y <= board.y + board.height * root.zoom
            if (!onBoard) root.blankChosen()
        }
    }
    DragHandler {
        target: board
        xAxis.minimum: -root.canvasWidth * root.zoom + 120
        xAxis.maximum: root.width - 120
        yAxis.minimum: -root.canvasHeight * root.zoom + 120
        yAxis.maximum: root.height - 120
    }
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function(event) {
            const factor = event.angleDelta.y > 0 ? 1.12 : 0.89
            root.zoom = Math.max(root.minZoom, Math.min(root.maxZoom, root.zoom * factor))
        }
    }
    PinchHandler {
        minimumScale: root.minZoom
        maximumScale: root.maxZoom
        onActiveScaleChanged: root.zoom = activeScale
    }
}
