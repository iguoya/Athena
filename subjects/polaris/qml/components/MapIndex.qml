import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 侧栏只按两大学科列目录：计算机 / 电子信息。每科下面是知识图谱与实践主干，
// 知识点作为子项始终列出。职业图仍在内容里，这里不出现，避免把培养阶段带跑。
Rectangle {
    id: root
    required property var maps
    required property string selectedMapId
    required property var mapNodes
    required property string selectedNodeId
    signal mapChosen(string mapId)
    signal nodeChosen(string nodeId)
    signal nodeHovered(string nodeId)
    color: "#08161C"

    readonly property var groupedMaps: {
        const computer = []
        const electronic = []
        for (let i = 0; i < maps.length; ++i) {
            const map = maps[i]
            if (map.view_kind !== "academic")
                continue
            const kind = root.disciplineOf(map)
            if (kind === "electronic")
                electronic.push(map)
            else if (kind === "computer")
                computer.push(map)
        }
        root.sortByRole(computer)
        root.sortByRole(electronic)
        const grouped = []
        const sections = [
            { title: "计算机", maps: computer },
            { title: "电子信息", maps: electronic }
        ]
        for (let s = 0; s < sections.length; ++s) {
            if (sections[s].maps.length === 0)
                continue
            grouped.push({ entryKind: "header", title: sections[s].title })
            for (let i = 0; i < sections[s].maps.length; ++i) {
                const map = sections[s].maps[i]
                grouped.push({
                    entryKind: "map",
                    map: map,
                    label: root.mapLabel(map)
                })
                root.appendNodes(grouped, map)
            }
        }
        return grouped
    }

    function disciplineOf(map) {
        const id = map.id || ""
        if (id.indexOf("electronic") === 0)
            return "electronic"
        if (id.indexOf("computer") === 0)
            return "computer"
        const nodes = map.nodes || []
        if (nodes.length > 0) {
            const nodeId = String(nodes[0].id || "")
            if (nodeId.indexOf("polaris.ei.") === 0)
                return "electronic"
            if (nodeId.indexOf("polaris.cs.") === 0)
                return "computer"
        }
        return ""
    }

    function sortByRole(list) {
        list.sort(function(a, b) {
            const left = a.graph_kind === "course" ? 0 : 1
            const right = b.graph_kind === "course" ? 0 : 1
            return left - right
        })
    }

    function mapLabel(map) {
        if (map.graph_kind === "course")
            return "知识图谱"
        return "实践主干"
    }

    function subtitleFor(map) {
        const count = (map.nodes || []).length
        if (map.graph_kind === "course")
            return count + " 门课"
        return count + " 项实践"
    }

    function appendNodes(grouped, map) {
        const source = map.nodes || []
        const grades = [
            { id: "essential", title: "必需" },
            { id: "important", title: "重要" },
            { id: "optional", title: "可选" }
        ]
        let used = 0
        for (let g = 0; g < grades.length; ++g) {
            const items = []
            for (let i = 0; i < source.length; ++i) {
                if ((source[i].priority || "") === grades[g].id)
                    items.push(source[i])
            }
            if (items.length === 0)
                continue
            grouped.push({ entryKind: "grade", title: grades[g].title })
            for (let i = 0; i < items.length; ++i)
                grouped.push({ entryKind: "node", node: items[i] })
            used += items.length
        }
        if (used > 0)
            return
        for (let i = 0; i < source.length; ++i)
            grouped.push({ entryKind: "node", node: source[i] })
    }

    function isCurrent(map) {
        return root.selectedMapId === map.id
    }

    function rowHeight(kind) {
        if (kind === "header") return 30
        if (kind === "grade") return 22
        if (kind === "node") return 34
        return 48
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 14

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                text: "北极星"
                color: "#D9F0EB"
                font.pixelSize: 26
                font.weight: Font.DemiBold
            }
            Text {
                Layout.fillWidth: true
                text: "学科路线图"
                color: "#A9C5C0"
                wrapMode: Text.WordWrap
                font.pixelSize: 14
                lineHeight: 1.3
                lineHeightMode: Text.ProportionalHeight
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#39515A" }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 3
            model: root.groupedMaps
            delegate: Item {
                id: row
                required property var modelData
                width: ListView.view.width
                height: root.rowHeight(modelData.entryKind)

                Loader {
                    anchors.fill: parent
                    sourceComponent: {
                        const kind = row.modelData.entryKind
                        if (kind === "header") return groupHeader
                        if (kind === "grade") return gradeHeader
                        if (kind === "node") return nodeEntry
                        return mapEntry
                    }
                }

                Component {
                    id: groupHeader
                    Text {
                        text: row.modelData.title
                        color: "#D9F0EB"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Component {
                    id: gradeHeader
                    Text {
                        text: row.modelData.title
                        color: "#8FB4AD"
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                        leftPadding: 10
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Component {
                    id: mapEntry
                    ItemDelegate {
                        id: entry
                        anchors.fill: parent
                        highlighted: root.isCurrent(row.modelData.map)
                        text: row.modelData.label
                        onClicked: root.mapChosen(row.modelData.map.id)
                        contentItem: Column {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: 10
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 2
                            Text {
                                width: parent.width
                                text: row.modelData.label
                                color: entry.highlighted ? "#FFFFFF" : "#E5EEEA"
                                font.pixelSize: 15
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Text {
                                width: parent.width
                                text: root.subtitleFor(row.modelData.map)
                                color: entry.highlighted ? "#BEE7DC" : "#9BB5B0"
                                font.pixelSize: 12
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

                Component {
                    id: nodeEntry
                    ItemDelegate {
                        id: nodeBtn
                        anchors.fill: parent
                        highlighted: (row.modelData.node.id || "") === root.selectedNodeId
                        onClicked: root.nodeChosen(row.modelData.node.id)
                        hoverEnabled: true
                        onHoveredChanged: {
                            if (hovered)
                                root.nodeHovered(row.modelData.node.id)
                            else
                                root.nodeHovered("")
                        }
                        contentItem: Text {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.leftMargin: 20
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            text: row.modelData.node.title
                            color: nodeBtn.highlighted ? "#FFFFFF" : "#C5D8D3"
                            font.pixelSize: 14
                            elide: Text.ElideRight
                        }
                        background: Rectangle {
                            radius: 8
                            color: nodeBtn.highlighted ? "#3D7A86"
                                                       : (nodeBtn.hovered ? "#1C3841" : "transparent")
                        }
                        ToolTip.visible: nodeBtn.hovered && Boolean(row.modelData.node.stable_definition)
                        ToolTip.text: {
                            const n = row.modelData.node
                            let text = "内容：" + (n.stable_definition || "")
                            if (n.engineering_role)
                                text += "\n用途：" + n.engineering_role
                            if (n.pitfall)
                                text += "\n难点：" + n.pitfall
                            return text
                        }
                        ToolTip.delay: 280
                        ToolTip.timeout: 12000
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            text: "点知识图谱看全图。点知识点进入这一课的详细介绍。"
            color: "#9BB5B0"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
    }
}
