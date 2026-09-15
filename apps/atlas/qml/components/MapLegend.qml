import QtQuick
import QtQuick.Layouts

RowLayout {
    spacing: 18
    Text { text: "能力域"; color: "#40575E"; font.pixelSize: 14; font.weight: Font.DemiBold }
    Repeater {
        model: [
            { color: "#2E6F78", label: "基础" },
            { color: "#4969A8", label: "软件" },
            { color: "#9A6632", label: "电子" },
            { color: "#8A557E", label: "控制" },
            { color: "#3B7E64", label: "计算" },
            { color: "#A2464B", label: "保障" }
        ]
        delegate: RowLayout {
            required property var modelData
            spacing: 5
            Rectangle { width: 9; height: 9; radius: 4.5; color: modelData.color }
            Text { text: modelData.label; color: "#5A6D72"; font.pixelSize: 13 }
        }
    }
    Item { Layout.fillWidth: true }
    Text { text: "验收：测量　·　基准　·　集成　·　评审　·　实线强先修　虚线使能"; color: "#5A6D72"; font.pixelSize: 13 }
}
