import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 右侧详情面板。它把一个节点的全部判断依据摊开：是什么、解决什么、难在哪、
// 为什么这个必要程度、支撑哪些目标能力、先做什么、怎么算过、出处。
//
// 没选中节点时它不留白，而是显示这张图的理论科目——那些科目不建节点（ADR 0009
// 第 7 条），如果面板上也不给它们位置，它们就彻底没有落点了。
Rectangle {
    id: root
    required property var node
    required property var edges
    signal closed()
    color: "#FFFFFF"
    border.color: "#D8DEDB"
    border.width: 1

    readonly property bool hasNode: Boolean(root.node && root.node.id)
    readonly property var crossLinks: root.hasNode ? atlas.crossEdgesFor(root.node.id) : []

    function mapIsLocked(mapId) {
        const maps = atlas.maps
        for (let i = 0; i < maps.length; ++i) {
            if (maps[i].id === mapId)
                return maps[i].view_kind !== "academic"
        }
        return true
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            x: 22
            width: Math.max(0, parent.width - 44)
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    text: root.hasNode ? "节点说明" : "如何阅读"
                    color: "#1A313A"
                    font.pixelSize: 20
                    font.weight: Font.DemiBold
                }
                ToolButton { visible: root.hasNode; text: "×"; onClicked: root.closed() }
            }

            // —— 未选中节点：讲怎么读这张图，并给理论科目一个落点 ——
            Text {
                visible: !root.hasNode
                Layout.fillWidth: true
                text: "从图上选一个节点，这里会展开它的定义、工程角色、难点、必要程度的判断依据、动手练习和验收口径。实线是强先修，虚线是「知道渊源会更透彻」的来路。"
                color: "#52666D"
                wrapMode: Text.WordWrap
                font.pixelSize: 16
                lineHeight: 1.28
            }

            ColumnLayout {
                visible: !root.hasNode && root.edges.length > 0
                Layout.fillWidth: true
                spacing: 10

                Label { text: "依赖编号（与图上圆点对应）"; font.bold: true }
                Repeater {
                    model: root.edges
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: (modelData.number || "") + ". "
                                + atlas.nodeTitle(modelData.from)
                                + " → "
                                + atlas.nodeTitle(modelData.to)
                                + (modelData.relation === "requires" ? "" : " · 来路，非门槛")
                            color: "#24424B"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.rationale || ""
                            color: "#5A6D72"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 13
                            lineHeight: 1.22
                        }
                    }
                }
            }

            ColumnLayout {
                visible: !root.hasNode && atlas.selectedMapTheory.length > 0
                Layout.fillWidth: true
                spacing: 10

                Label { text: "理论科目（不建节点）"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: "它们没有可上手验证的实验，所以不在图上占节点；配合教材了解即可。"
                    color: "#62777E"
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                    lineHeight: 1.24
                }
                Repeater {
                    model: atlas.selectedMapTheory
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3
                        Text {
                            Layout.fillWidth: true
                            text: modelData.name
                            color: "#24424B"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.content
                            color: "#4A5F66"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            lineHeight: 1.22
                        }
                        Text {
                            Layout.fillWidth: true
                            text: "起什么作用：" + modelData.role
                            color: "#62777E"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            lineHeight: 1.22
                        }
                    }
                }
            }

            // —— 选中节点 ——
            ColumnLayout {
                visible: root.hasNode
                Layout.fillWidth: true
                spacing: 12

                Text {
                    Layout.fillWidth: true
                    text: root.node.title || ""
                    color: "#152D36"
                    wrapMode: Text.WordWrap
                    font.pixelSize: 25
                    font.weight: Font.DemiBold
                }
                Rectangle {
                    Layout.fillWidth: true
                    height: 4
                    radius: 2
                    color: atlas.trackColor(root.node.track || "")
                }
                Text {
                    Layout.fillWidth: true
                    text: atlas.priorityLabel(root.node.priority || "")
                        + " · " + atlas.volatilityLabel(root.node.volatility || "")
                        + " · " + atlas.validationLabel(root.node.validation || "")
                    color: atlas.priorityColor(root.node.priority || "")
                    wrapMode: Text.WordWrap
                    font.pixelSize: 14
                }

                Label { text: "它是什么"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: root.node.stable_definition || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Label { text: "工程中解决什么"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: root.node.engineering_role || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Label { visible: Boolean(root.node.pitfall); text: "难在哪"; font.bold: true }
                Text {
                    visible: Boolean(root.node.pitfall)
                    Layout.fillWidth: true
                    text: root.node.pitfall || ""
                    wrapMode: Text.WordWrap
                    color: "#8A4B3F"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Label { visible: Boolean(root.node.priority_reason); text: "为什么是这个必要程度"; font.bold: true }
                Text {
                    visible: Boolean(root.node.priority_reason)
                    Layout.fillWidth: true
                    text: root.node.priority_reason || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Text {
                    visible: Boolean(root.node.targets && root.node.targets.length > 0)
                    Layout.fillWidth: true
                    text: "职业方向与目标待知识体系补全后解锁，这一阶段不按就业落点组织学习。"
                    wrapMode: Text.WordWrap
                    color: "#7A8F94"
                    font.pixelSize: 14
                    lineHeight: 1.22
                }

                Label { text: "先做什么"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: root.node.practice || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Label { text: "如何验证"; font.bold: true }
                Text {
                    Layout.fillWidth: true
                    text: root.node.validation_note || ""
                    wrapMode: Text.WordWrap
                    color: "#40545B"
                    font.pixelSize: 16
                    lineHeight: 1.24
                }

                Text {
                    visible: Boolean(root.node.app)
                    Layout.fillWidth: true
                    text: "这个领域由「" + (root.node.app || "") + "」应用承载，学习与练习在那里进行。"
                    wrapMode: Text.WordWrap
                    color: "#3C6B63"
                    font.pixelSize: 14
                    lineHeight: 1.24
                }

                // 拆成多张图之后，一部分先修关系的两端落在不同图里。不显示出来，
                // 这些依赖就等于因为拆图而消失了（ADR 0009 第 6 条）。
                Label {
                    visible: root.crossLinks.length > 0
                    text: "跨图关联"
                    font.bold: true
                }
                Repeater {
                    model: root.crossLinks
                    delegate: ColumnLayout {
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 3

                        Text {
                            Layout.fillWidth: true
                            text: (modelData.incoming ? "前置：" : "它支撑：")
                                + modelData.peer_title
                                + "（" + modelData.map_title + "）"
                                + (modelData.strong ? "" : " · 来路，非门槛")
                            color: crossHover.hovered ? "#1F4E58" : "#35606A"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 15
                            font.underline: crossHover.hovered
                            HoverHandler { id: crossHover }
                            TapHandler {
                                enabled: !root.mapIsLocked(modelData.map_id || "")
                                onTapped: {
                                    atlas.openMap(modelData.map_id)
                                    atlas.selectNode(modelData.peer_id)
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.rationale
                            color: "#5A6D72"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 14
                            lineHeight: 1.22
                        }
                    }
                }

                Label { text: "来源"; font.bold: true }
                Repeater {
                    model: root.node.source_refs || []
                    delegate: Text {
                        required property var modelData
                        Layout.fillWidth: true
                        text: "• " + modelData.source_id + " · " + modelData.locator
                        color: "#55727A"
                        wrapMode: Text.WordWrap
                        font.pixelSize: 14
                    }
                }
            }
        }
    }
}
