import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    required property var maps
    required property string selectedMapId
    signal mapChosen(string mapId)
    color: "#132B35"

    readonly property var groupedMaps: {
        const system = []
        const support = []
        const playbook = []
        const reference = []
        const adjacent = []
        for (let i = 0; i < maps.length; ++i) {
            const emphasis = maps[i].emphasis
            if (emphasis === "reference") reference.push(maps[i])
            else if (emphasis === "adjacent") adjacent.push(maps[i])
            else if (emphasis === "support") support.push(maps[i])
            else if (maps[i].family === "playbook") playbook.push(maps[i])
            else system.push(maps[i])
        }
        // muted 的分组在视觉上退一层：参考资料不该和主干抢注意力。
        const grouped = []
        const groups = [
            { title: "体系主干", maps: system, muted: false },
            { title: "助力方向", maps: support, muted: false },
            { title: "实操地图", maps: playbook, muted: false },
            { title: "重要参考", maps: reference, muted: false },
            { title: "相邻参考", maps: adjacent, muted: true }
        ]
        for (let g = 0; g < groups.length; ++g) {
            if (groups[g].maps.length === 0)
                continue
            grouped.push({ entryKind: "header", title: groups[g].title, muted: groups[g].muted })
            for (let i = 0; i < groups[g].maps.length; ++i)
                grouped.push({ entryKind: "map", map: groups[g].maps[i], muted: groups[g].muted })
        }
        return grouped
    }

    function subtitleFor(map) {
        if (map.emphasis === "support") return "研制辅助 · 不进飞控"
        if (map.emphasis === "reference") return "十七所对照 · 不与主干平级"
        if (map.emphasis === "adjacent") return "相邻领域 · 低于主干"
        if (map.family === "playbook") return "书 / 方案 / 可交付练习"
        return map.view_kind === "academic" ? "学科视图" : "工程 / 研制投影"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 16

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: "ATLAS"
                color: "#D9F0EB"
                font.pixelSize: 28
                font.letterSpacing: 2
                font.weight: Font.Bold
            }
            Text {
                Layout.fillWidth: true
                text: "软硬融合技术体系图谱"
                color: "#A9C5C0"
                wrapMode: Text.WordWrap
                font.pixelSize: 15
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#39515A" }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 6
            model: root.groupedMaps
            delegate: Item {
                id: row
                required property var modelData
                width: ListView.view.width
                height: modelData.entryKind === "header" ? 28 : 72

                // 两种行的字段不同：分组标题没有 map。visible 挡不住绑定求值，
                // 所以按行类型各加载各的，而不是叠两层再互相隐藏。
                Loader {
                    anchors.fill: parent
                    sourceComponent: row.modelData.entryKind === "header" ? groupHeader : mapEntry
                }

                Component {
                    id: groupHeader
                    Text {
                        text: row.modelData.title
                        color: row.modelData.muted ? "#7A9A95" : "#D9F0EB"
                        font.pixelSize: row.modelData.muted ? 13 : 15
                        font.weight: row.modelData.muted ? Font.Medium : Font.DemiBold
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Component {
                    id: mapEntry
                    ItemDelegate {
                        id: entry
                        anchors.fill: parent
                        highlighted: root.selectedMapId === row.modelData.map.id
                        text: row.modelData.map.title
                        opacity: row.modelData.muted && !highlighted ? 0.72 : 1
                        onClicked: root.mapChosen(row.modelData.map.id)
                        contentItem: Column {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: 12
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 4
                            Text {
                                width: parent.width
                                text: row.modelData.map.title
                                color: entry.highlighted ? "#FFFFFF" : "#E5EEEA"
                                font.pixelSize: row.modelData.muted ? 15 : 16
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Text {
                                width: parent.width
                                text: root.subtitleFor(row.modelData.map)
                                color: entry.highlighted ? "#BEE7DC" : "#9BB5B0"
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }
                        }
                        background: Rectangle {
                            radius: 10
                            color: entry.highlighted ? "#316B78"
                                                     : (entry.hovered ? "#203D47" : "transparent")
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: "主干用实时与高性能从软件调度、硬件通路两侧验收。十七所实时控制放在重要参考，机器人放在相邻参考，都不与主干平级。实线是强先修，虚线是使能。"
            color: "#9BB5B0"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
    }
}
