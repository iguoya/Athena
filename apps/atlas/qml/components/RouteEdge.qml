import QtQuick
import QtQuick.Shapes

// 航路走场景图曲线，不走 CPU Canvas。缩放、流动和选中高亮都在 GPU 上完成。
Item {
    id: root
    required property var modelData
    required property string focusId
    required property real flowPhase
    required property var inspectedEdge

    readonly property bool strong: modelData.strong === true
    readonly property bool focusing: focusId.length > 0
    readonly property bool related: !focusing || modelData.from === focusId || modelData.to === focusId
    readonly property bool inspect: inspectedEdge && inspectedEdge.number === modelData.number
    readonly property real x0: modelData.x0
    readonly property real y0: modelData.y0
    readonly property real x1: modelData.x1
    readonly property real y1: modelData.y1
    readonly property real mid: modelData.mid
    readonly property color ink: {
        if (inspect)
            return "#FFB37A"
        if (related && focusing)
            return strong ? "#7EF0D4" : "#C9D6A8"
        return strong ? "#6AA8A0" : "#6E8490"
    }

    width: parent ? parent.width : 0
    height: parent ? parent.height : 0
    opacity: related ? 1 : 0.14
    z: inspect ? 3 : 1
    Behavior on opacity { NumberAnimation { duration: 160 } }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        antialiasing: true
        ShapePath {
            strokeColor: Qt.rgba(root.ink.r, root.ink.g, root.ink.b, related && focusing ? 0.28 : 0)
            strokeWidth: 11
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathMove { x: root.x0; y: root.y0 }
            PathCubic {
                control1X: root.x0; control1Y: root.mid
                control2X: root.x1; control2Y: root.mid
                x: root.x1; y: root.y1 - 10
            }
        }
        ShapePath {
            strokeColor: root.ink
            strokeWidth: root.inspect ? 5.2 : (root.related && root.focusing ? 3.6 : (root.strong ? 2.6 : 1.8))
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            dashPattern: root.strong ? [] : [8, 10]
            dashOffset: root.strong ? 0 : -root.flowPhase * 36
            PathMove { x: root.x0; y: root.y0 }
            PathCubic {
                control1X: root.x0; control1Y: root.mid
                control2X: root.x1; control2Y: root.mid
                x: root.x1; y: root.y1 - 10
            }
        }
        ShapePath {
            strokeWidth: 0
            fillColor: root.ink
            PathMove { x: root.x1; y: root.y1 }
            PathLine { x: root.x1 - 7; y: root.y1 - 12 }
            PathLine { x: root.x1 + 7; y: root.y1 - 12 }
            PathLine { x: root.x1; y: root.y1 }
        }
    }

    Repeater {
        model: root.strong && root.related ? 2 : 0
        delegate: Rectangle {
            required property int index
            width: 8
            height: 8
            radius: 4
            color: "#E7FFF7"
            opacity: 0.35 + 0.55 * Math.sin((traveller.progress) * Math.PI)
            x: traveller.x - 4
            y: traveller.y - 4
            PathInterpolator {
                id: traveller
                progress: (root.flowPhase + index * 0.5) % 1
                path: Path {
                    startX: root.x0
                    startY: root.y0
                    PathCubic {
                        control1X: root.x0; control1Y: root.mid
                        control2X: root.x1; control2Y: root.mid
                        x: root.x1; y: root.y1 - 10
                    }
                }
            }
        }
    }
}
