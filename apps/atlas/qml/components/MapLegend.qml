import QtQuick
import QtQuick.Layouts

RowLayout {
    id: root
    required property var nodes
    spacing: 18

    readonly property var tracksInUse: {
        const seen = []
        const labels = []
        for (let i = 0; i < nodes.length; ++i) {
            const track = nodes[i].track
            if (!track || seen.indexOf(track) >= 0)
                continue
            seen.push(track)
            labels.push({ color: atlas.trackColor(track), label: atlas.trackLabel(track) })
        }
        return labels
    }

    Text { text: "能力域"; color: "#40575E"; font.pixelSize: 14; font.weight: Font.DemiBold }
    Repeater {
        model: root.tracksInUse
        delegate: RowLayout {
            required property var modelData
            spacing: 5
            Rectangle { width: 9; height: 9; radius: 4.5; color: modelData.color }
            Text { text: modelData.label; color: "#5A6D72"; font.pixelSize: 13 }
        }
    }
    Item { Layout.fillWidth: true }
    Text { text: "侧栏按必需 / 重要 / 可选罗列　·　实线门槛　虚线来路　·　▶ 入门可任选起步"; color: "#5A6D72"; font.pixelSize: 13 }
}
