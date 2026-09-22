import QtQuick

// 用三盏灯表示必需 / 重要 / 可选，不靠一段说明。
Row {
    id: root
    property string priority: "important"
    property int lamp: 10
    property bool compact: true
    spacing: Math.max(3, lamp * 0.3)

    readonly property int filled: priority === "essential" ? 3 : (priority === "optional" ? 1 : 2)
    readonly property color onColor: priority === "essential" ? "#2E8F7A"
                                 : (priority === "optional" ? "#8A7A4A" : "#3D7A86")

    Repeater {
        model: 3
        delegate: Rectangle {
            required property int index
            width: root.lamp
            height: root.lamp
            radius: root.lamp / 2
            color: index < root.filled ? root.onColor : "#33455A60"
            border.color: index < root.filled ? "#A5F0DE" : "#44555C"
            border.width: 1
        }
    }
}
