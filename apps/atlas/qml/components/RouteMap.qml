import QtQuick
import QtQuick.Controls
import QtQuick.Particles
import QtQuick.Shapes

// 航海星图式知识图谱：分层是地形，节点是灯塔，实线是航路，虚线是来路。
// 单击选点看清邻域，双击或点「进入」才进专页。编号航标可点开依赖理由。
Item {
    id: root
    required property var nodes
    required property var edges
    required property int canvasWidth
    required property int canvasHeight
    required property string selectedNodeId
    property string hoveredNodeId: ""
    property string layerFilter: ""
    property var inspectedEdge: null

    signal nodeChosen(string nodeId)
    signal nodeOpened(string nodeId)
    signal blankChosen()

    clip: true

    property real zoom: 0.72
    property real minZoom: 0.38
    property real maxZoom: 1.46
    property real flowPhase: 0

    readonly property string focusId: hoveredNodeId || selectedNodeId
    readonly property var litIds: {
        const set = {}
        const id = root.focusId
        if (!id)
            return set
        set[id] = true
        for (let i = 0; i < root.edges.length; ++i) {
            const edge = root.edges[i]
            if (edge.from === id)
                set[edge.to] = true
            if (edge.to === id)
                set[edge.from] = true
        }
        return set
    }

    readonly property var strata: {
        const buckets = {}
        const order = []
        for (let i = 0; i < root.nodes.length; ++i) {
            const node = root.nodes[i]
            if (!root.layerVisible(node))
                continue
            const key = String(node.layer ?? node.priority ?? i)
            if (!buckets[key]) {
                buckets[key] = {
                    key: key,
                    minY: node.y,
                    maxY: node.y + node.h,
                    priority: node.priority || ""
                }
                order.push(key)
            } else {
                buckets[key].minY = Math.min(buckets[key].minY, node.y)
                buckets[key].maxY = Math.max(buckets[key].maxY, node.y + node.h)
            }
        }
        const bands = []
        for (let i = 0; i < order.length; ++i)
            bands.push(buckets[order[i]])
        bands.sort(function(a, b) { return a.minY - b.minY })
        return bands
    }

    readonly property var edgeMarks: root.buildEdgeMarks()
    readonly property var hoveredNode: root.nodeById(root.hoveredNodeId)
    readonly property var degreeOf: {
        const d = {}
        for (let i = 0; i < root.nodes.length; ++i)
            d[root.nodes[i].id] = { inbound: 0, outbound: 0 }
        for (let i = 0; i < root.edges.length; ++i) {
            const edge = root.edges[i]
            if (d[edge.from])
                d[edge.from].outbound += 1
            if (d[edge.to])
                d[edge.to].inbound += 1
        }
        return d
    }

    function degreeIn(id) {
        const d = root.degreeOf[id]
        return d ? d.inbound : 0
    }
    function degreeOut(id) {
        const d = root.degreeOf[id]
        return d ? d.outbound : 0
    }

    function nodeById(id) {
        if (!id)
            return null
        for (let i = 0; i < root.nodes.length; ++i) {
            if (root.nodes[i].id === id)
                return root.nodes[i]
        }
        return null
    }

    function layerVisible(node) {
        if (!root.layerFilter)
            return true
        return (node.priority || "") === root.layerFilter
    }

    function isLit(nodeId) {
        if (!root.focusId)
            return true
        return root.litIds[nodeId] === true
    }

    function stratumTitle(priority) {
        if (priority === "essential") return "必需"
        if (priority === "important") return "重要"
        if (priority === "optional") return "可选"
        return ""
    }

    function stratumColor(priority) {
        if (priority === "essential") return "#143F3A"
        if (priority === "important") return "#1B3344"
        if (priority === "optional") return "#2A2438"
        return "#173038"
    }

    function bezierPoint(x0, y0, x1, y1, t) {
        const mid = (y0 + y1) / 2
        const y3 = y1 - 10
        const u = 1 - t
        return {
            x: u * u * u * x0 + 3 * u * u * t * x0 + 3 * u * t * t * x1 + t * t * t * x1,
            y: u * u * u * y0 + 3 * u * u * t * mid + 3 * u * t * t * mid + t * t * t * y3
        }
    }

    function buildEdgeMarks() {
        const marks = []
        const byId = {}
        for (let i = 0; i < root.nodes.length; ++i)
            byId[root.nodes[i].id] = root.nodes[i]
        for (let i = 0; i < root.edges.length; ++i) {
            const edge = root.edges[i]
            const from = byId[edge.from]
            const to = byId[edge.to]
            if (!from || !to)
                continue
            if (!root.layerVisible(from) || !root.layerVisible(to))
                continue
            const x0 = from.x + from.w / 2
            const y0 = from.y + from.h
            const x1 = to.x + to.w / 2
            const y1 = to.y
            const radius = 13
            const lean = x0 < x1 - 1 ? -(radius + 6) : (x0 > x1 + 1 ? radius + 6 : 0)
            marks.push({
                number: edge.number || (i + 1),
                from: edge.from,
                to: edge.to,
                relation: edge.relation,
                rationale: edge.rationale || "",
                strong: edge.relation === "requires",
                x0: x0,
                y0: y0,
                x1: x1,
                y1: y1,
                mid: (y0 + y1) / 2,
                x: x1 + lean - radius,
                y: y1 - radius * 2 - 6,
                size: radius * 2
            })
        }
        return marks
    }

    function resetView() {
        const fitted = Math.min(width / Math.max(1, canvasWidth), height / Math.max(1, canvasHeight)) * 0.9
        zoom = Math.min(0.92, Math.max(minZoom, fitted))
        board.x = Math.round((width - canvasWidth * zoom) / 2)
        board.y = Math.max(28, Math.round((height - canvasHeight * zoom) / 2))
    }

    function flyTo(nodeId) {
        const node = nodeById(nodeId)
        if (!node)
            return
        const targetZoom = Math.min(root.maxZoom, Math.max(root.zoom, 0.94))
        const cx = node.x + node.w / 2
        const cy = node.y + node.h / 2
        zoomAnim.to = targetZoom
        boardXAnim.to = root.width / 2 - cx * targetZoom
        boardYAnim.to = root.height / 2 - cy * targetZoom
        zoomAnim.restart()
        boardXAnim.restart()
        boardYAnim.restart()
    }

    NumberAnimation { id: zoomAnim; target: root; property: "zoom"; duration: 480; easing.type: Easing.InOutCubic }
    NumberAnimation { id: boardXAnim; target: board; property: "x"; duration: 480; easing.type: Easing.InOutCubic }
    NumberAnimation { id: boardYAnim; target: board; property: "y"; duration: 480; easing.type: Easing.InOutCubic }

    function clearInspect() {
        inspectedEdge = null
        hoveredNodeId = ""
    }

    Component.onCompleted: resetView()
    onCanvasWidthChanged: resetView()
    onCanvasHeightChanged: resetView()

    FrameAnimation {
        running: root.visible && root.opacity > 0.5
        onTriggered: root.flowPhase = (root.flowPhase + Math.min(0.04, frameTime * 0.32)) % 1
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#07151A" }
            GradientStop { position: 0.55; color: "#0C242C" }
            GradientStop { position: 1.0; color: "#102C33" }
        }
    }

    ParticleSystem {
        id: dust
        anchors.fill: parent
        z: 0
        paused: !root.visible || root.opacity < 0.5
        ItemParticle {
            fade: true
            delegate: Rectangle {
                width: 3
                height: 3
                radius: 1.5
                color: "#A5F0DE"
                opacity: 0.55
            }
        }
        Emitter {
            anchors.fill: parent
            emitRate: 8
            lifeSpan: 5400
            lifeSpanVariation: 1600
            size: 3
            velocity: AngleDirection {
                angle: 108
                angleVariation: 36
                magnitude: 16
                magnitudeVariation: 10
            }
        }
    }

    Repeater {
        model: 22
        delegate: Rectangle {
            required property int index
            width: index % 4 === 0 ? 2 : 1
            height: 1
            radius: 1
            color: "#7EE8D2"
            opacity: 0.08 + (index % 5) * 0.02
            x: (index * 73 + mote.xShift) % Math.max(1, root.width)
            y: (index * 47 + mote.yShift) % Math.max(1, root.height)
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { from: 0.04; to: 0.22; duration: 1400 + index * 90 }
                NumberAnimation { from: 0.22; to: 0.04; duration: 1600 + index * 70 }
            }
            NumberAnimation on x {
                id: mote
                property real xShift: 0
                property real yShift: index * 17
                running: false
            }
        }
    }

    Item {
        id: board
        width: root.canvasWidth
        height: root.canvasHeight
        scale: root.zoom
        transformOrigin: Item.TopLeft

        Repeater {
            model: root.strata
            delegate: Rectangle {
                required property var modelData
                x: 24
                y: modelData.minY - 28
                width: board.width - 48
                height: modelData.maxY - modelData.minY + 56
                radius: 28
                color: root.stratumColor(modelData.priority)
                opacity: 0.55
                border.color: "#2E5A5C"
                border.width: 1
                MapText {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.leftMargin: 18
                    anchors.topMargin: 10
                    text: root.stratumTitle(modelData.priority)
                    color: "#9AD7C8"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    opacity: 0.9
                }
            }
        }

        Canvas {
            anchors.fill: parent
            z: 0
            onPaint: {
                const ctx = getContext("2d")
                ctx.reset()
                ctx.strokeStyle = "rgba(126, 196, 188, 0.08)"
                ctx.lineWidth = 1
                const step = 86
                for (let x = 40; x < width; x += step) {
                    ctx.beginPath()
                    ctx.moveTo(x, 20)
                    ctx.lineTo(x, height - 20)
                    ctx.stroke()
                }
                for (let y = 40; y < height; y += step) {
                    ctx.beginPath()
                    ctx.moveTo(20, y)
                    ctx.lineTo(width - 20, y)
                    ctx.stroke()
                }
            }
        }

        Repeater {
            model: root.edgeMarks
            delegate: RouteEdge {
                required property var modelData
                focusId: root.focusId
                flowPhase: root.flowPhase
                inspectedEdge: root.inspectedEdge
            }
        }

        Repeater {
            model: root.nodes
            delegate: RouteNode {
                required property var modelData
                z: selected || hovered ? 8 : 2
                node: modelData
                selected: root.selectedNodeId === modelData.id
                hovered: root.hoveredNodeId === modelData.id
                lit: root.isLit(modelData.id)
                visible: root.layerVisible(modelData)
                x: modelData.x
                y: modelData.y
                inbound: root.degreeIn(modelData.id)
                outbound: root.degreeOut(modelData.id)
                onEntered: root.hoveredNodeId = modelData.id
                onExited: {
                    if (root.hoveredNodeId === modelData.id)
                        root.hoveredNodeId = ""
                }
                onChosen: function(id) {
                    root.inspectedEdge = null
                    root.nodeChosen(id)
                }
                onOpened: function(id) { root.nodeOpened(id) }
            }
        }

        Repeater {
            model: root.edgeMarks
            delegate: Item {
                required property var modelData
                x: modelData.x
                y: modelData.y
                width: modelData.size
                height: modelData.size
                z: 12
                property bool active: root.inspectedEdge && root.inspectedEdge.number === modelData.number
                Rectangle {
                    anchors.fill: parent
                    radius: width / 2
                    color: active ? "#FFB37A" : (modelData.strong ? "#128C7A" : "#5C6B75")
                    border.color: "#E7FFF7"
                    border.width: active || markHover.hovered ? 2 : 0
                    scale: markHover.hovered || active ? 1.12 : 1
                    Behavior on scale { NumberAnimation { duration: 120 } }
                    MapText {
                        anchors.centerIn: parent
                        text: String(modelData.number)
                        color: "#FFFFFF"
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }
                }
                HoverHandler { id: markHover }
                TapHandler {
                    onTapped: root.inspectedEdge = modelData
                }
            }
        }

        Rectangle {
            visible: Boolean(root.hoveredNode)
            x: {
                const node = root.hoveredNode
                if (!node)
                    return 0
                return node.x + node.w + 16 > board.width - 300 ? node.x - 296 : node.x + node.w + 16
            }
            y: root.hoveredNode ? root.hoveredNode.y : 0
            width: 280
            height: captionColumn.height + 28
            radius: 16
            z: 16
            color: "#CC10262C"
            border.color: "#6FE0C8"
            border.width: 1
            Column {
                id: captionColumn
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 14
                spacing: 10
                MapText {
                    width: parent.width
                    text: root.hoveredNode ? (root.hoveredNode.title || "") : ""
                    color: "#E7FFF7"
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Row {
                    spacing: 10
                    PriorityMeter {
                        priority: root.hoveredNode ? (root.hoveredNode.priority || "") : ""
                        lamp: 9
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    TrackGlyph {
                        track: root.hoveredNode ? (root.hoveredNode.track || "") : ""
                        ink: root.hoveredNode ? atlas.trackColor(root.hoveredNode.track) : "#4AD4B2"
                        width: 18
                        height: 18
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                Row {
                    spacing: 16
                    MapText {
                        text: "◀ " + (root.hoveredNode ? root.degreeIn(root.hoveredNode.id) : 0)
                        color: "#7EF0D4"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                    }
                    MapText {
                        text: (root.hoveredNode ? root.degreeOut(root.hoveredNode.id) : 0) + " ▶"
                        color: "#7EB6E8"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                    }
                }
            }
        }
    }

    // 图名题签，像航海图角落的图廓。
    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.leftMargin: 22
        anchors.topMargin: 18
        width: Math.min(parent.width * 0.62, titleColumn.implicitWidth + 36)
        height: titleColumn.implicitHeight + 24
        radius: 16
        color: "#AA0E242B"
        border.color: "#3D6F70"
        border.width: 1
        Column {
            id: titleColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 4
            MapText {
                width: parent.width
                text: atlas.selectedMapTitle || atlas.title
                color: "#E8F7F2"
                font.pixelSize: 22
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Row {
                spacing: 6
                Repeater {
                    model: [
                        { id: "essential", color: "#2E8F7A" },
                        { id: "important", color: "#3D7A86" },
                        { id: "optional", color: "#8A7A4A" }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        height: 8
                        radius: 4
                        width: {
                            let n = 0
                            const nodes = root.nodes
                            for (let i = 0; i < nodes.length; ++i) {
                                if ((nodes[i].priority || "") === modelData.id)
                                    n += 1
                            }
                            const total = Math.max(1, nodes.length)
                            return Math.max(8, 120 * n / total)
                        }
                        color: modelData.color
                    }
                }
            }
        }
    }

    Item {
        width: 92
        height: 92
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: 16
        anchors.topMargin: 14
        Shape {
            anchors.fill: parent
            antialiasing: true
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: "#6FE0C8"
                strokeWidth: 1.6
                fillColor: "#C80E242B"
                PathAngleArc {
                    centerX: 46
                    centerY: 46
                    radiusX: 40
                    radiusY: 40
                    startAngle: 0
                    sweepAngle: 360
                }
            }
            ShapePath {
                strokeWidth: 0
                fillColor: "#4AD4B2"
                PathMove { x: 46; y: 12 }
                PathLine { x: 54; y: 46 }
                PathLine { x: 46; y: 80 }
                PathLine { x: 38; y: 46 }
                PathLine { x: 46; y: 12 }
            }
        }
        Shape {
            anchors.fill: parent
            antialiasing: true
            RotationAnimator on rotation {
                from: 0
                to: 360
                duration: 48000
                loops: Animation.Infinite
                running: root.visible && root.opacity > 0.5
            }
            ShapePath {
                strokeColor: "#336FE0C8"
                strokeWidth: 1
                fillColor: "transparent"
                PathAngleArc {
                    centerX: 46
                    centerY: 46
                    radiusX: 34
                    radiusY: 34
                    startAngle: 8
                    sweepAngle: 44
                }
            }
            ShapePath {
                strokeColor: "#336FE0C8"
                strokeWidth: 1
                fillColor: "transparent"
                PathAngleArc {
                    centerX: 46
                    centerY: 46
                    radiusX: 34
                    radiusY: 34
                    startAngle: 188
                    sweepAngle: 44
                }
            }
        }
        MapText {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 8
            text: "先修"
            color: "#E7FFF7"
            font.pixelSize: 11
            font.weight: Font.DemiBold
        }
    }

    Rectangle {
        anchors.left: parent.left
        width: 90
        height: parent.height
        z: 18
        enabled: false
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#9907151A" }
            GradientStop { position: 1.0; color: "#0007151A" }
        }
    }
    Rectangle {
        anchors.right: parent.right
        width: 90
        height: parent.height
        z: 18
        enabled: false
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#0007151A" }
            GradientStop { position: 1.0; color: "#9907151A" }
        }
    }

    MapText {
        visible: atlas.error.length > 0
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: 96
        anchors.margins: 24
        color: "#FF8B7A"
        text: atlas.error
        wrapMode: Text.WordWrap
        font.pixelSize: 16
        z: 20
    }

    TapHandler {
        acceptedButtons: Qt.LeftButton
        onTapped: function(eventPoint) {
            const position = eventPoint.position
            const onBoard = position.x >= board.x && position.x <= board.x + board.width * root.zoom
                && position.y >= board.y && position.y <= board.y + board.height * root.zoom
            if (!onBoard) {
                root.inspectedEdge = null
                root.blankChosen()
            }
        }
    }
    DragHandler {
        target: board
        xAxis.minimum: -root.canvasWidth * root.zoom + 160
        xAxis.maximum: root.width - 160
        yAxis.minimum: -root.canvasHeight * root.zoom + 160
        yAxis.maximum: root.height - 120
    }
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function(event) {
            const oldZoom = root.zoom
            const factor = event.angleDelta.y > 0 ? 1.12 : 0.89
            const next = Math.max(root.minZoom, Math.min(root.maxZoom, oldZoom * factor))
            const pos = event.position
            board.x = pos.x - (pos.x - board.x) * (next / oldZoom)
            board.y = pos.y - (pos.y - board.y) * (next / oldZoom)
            root.zoom = next
            event.accepted = true
        }
    }
    PinchHandler {
        property real startZoom: 1
        minimumScale: 0.3
        maximumScale: 3
        onActiveChanged: {
            if (active)
                startZoom = root.zoom
        }
        onScaleChanged: {
            if (active)
                root.zoom = Math.max(root.minZoom, Math.min(root.maxZoom, startZoom * scale))
        }
    }
}
