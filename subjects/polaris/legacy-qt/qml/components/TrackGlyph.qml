import QtQuick
import QtQuick.Shapes

// 能力域用符号，不写类别名。颜色仍走 polaris.trackColor。
Item {
    id: root
    property string track: ""
    property color ink: "#4AD4B2"
    width: 22
    height: 22

    Shape {
        anchors.fill: parent
        antialiasing: true
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: root.ink
            strokeWidth: 1.6
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg {
                path: {
                    switch (root.track) {
                    case "language":
                        return "M4 6 L10 18 L12 18 L18 6 M8 12 H16"
                    case "systems":
                        return "M4 16 V8 H8 V16 M10 16 V4 H14 V16 M16 16 V10 H20 V16"
                    case "hardware":
                    case "electronics":
                        return "M3 11 H8 L10 6 L14 16 L16 11 H21"
                    case "engineering":
                        return "M4 17 L11 4 L18 17 Z M7.5 12 H14.5"
                    case "ai":
                    case "compute":
                        return "M11 4 L18 8 V16 L11 20 L4 16 V8 Z M11 8 V16"
                    case "control":
                        return "M4 11 H20 M16 6 L20 11 L16 16"
                    case "capstone":
                    case "assurance":
                        return "M4 16 L11 4 L18 16 Z"
                    case "software":
                        return "M6 7 L3 11 L6 15 M16 7 L19 11 L16 15"
                    default:
                        return "M4 11 H18 M11 4 V18"
                    }
                }
            }
        }
    }
}
