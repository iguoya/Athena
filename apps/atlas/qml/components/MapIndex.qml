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
        // 三层，自下而上：学科入口是通用底盘，职业方向是大方向，职业目标是
        // 具体落点（某所研制口径那套认知）。分组只读 view_kind——地位一旦进了
        // 分组名，图谱就会被某个外部标尺重划一次（ADR 0054）。
        const discipline = []
        const direction = []
        const target = []
        for (let i = 0; i < maps.length; ++i) {
            const map = maps[i]
            if (map.view_kind === "academic") discipline.push(map)
            else if (map.view_kind === "target") target.push(map)
            else direction.push(map)
        }
        const grouped = []
        const groups = [
            { title: "技术体系", maps: discipline, muted: false },
            { title: "职业方向", maps: direction, muted: false },
            { title: "职业目标", maps: target, muted: false }
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
        // 职业目标层每张图自带定位（研制主干 / 地面助力 / 某所对照 / 相邻领域），
        // 这些差别是那套认知的一部分，不该在界面上被抹平成一个词。
        if (map.standing) return map.standing
        if (map.view_kind === "academic") return "学科入口 · 通用技术底盘"
        if (map.view_kind === "engineering") return "工程系统 · 高阶标尺"
        return "职业方向"
    }

    function isCurrent(map) {
        return root.selectedMapId === map.id
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
                        highlighted: root.isCurrent(row.modelData.map)
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
            text: "学科入口是通用底盘，职业方向是大方向，职业目标是具体落点。每个节点都给出稳定定义、工程角色、动手练习和验收方式。实线是强先修，虚线是使能。"
            color: "#9BB5B0"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
    }
}
