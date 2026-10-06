import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 知识点专页：原 C++ 首页的内容 / 用途 / 难点 / 需要放在最前面，
// 先修理由全文一起摊开；流程图和必要性在后面，不再把原文挤进剩余高度。
Item {
    id: root
    required property var node
    signal closed()

    readonly property bool hasNode: Boolean(root.node && root.node.id)
    readonly property color accent: polaris.trackColor(root.node.track || "")
    readonly property var inbound: root.collect("to")
    readonly property var outbound: root.collect("from")
    readonly property var crossLinks: root.hasNode ? polaris.crossEdgesFor(root.node.id) : []
    function collect(side) {
        const here = root.node.id || ""
        const list = []
        const edges = polaris.edges || []
        for (let i = 0; i < edges.length; ++i) {
            const edge = edges[i]
            if (side === "to" && edge.to === here)
                list.push({
                    id: edge.from,
                    title: polaris.nodeTitle(edge.from),
                    strong: edge.relation === "requires",
                    rationale: edge.rationale || ""
                })
            if (side === "from" && edge.from === here)
                list.push({
                    id: edge.to,
                    title: polaris.nodeTitle(edge.to),
                    strong: edge.relation === "requires",
                    rationale: edge.rationale || ""
                })
        }
        return list
    }

    function mapIsLocked(mapId) {
        const maps = polaris.maps
        for (let i = 0; i < maps.length; ++i) {
            if (maps[i].id === mapId)
                return maps[i].view_kind !== "academic"
        }
        return true
    }

    Rectangle {
        anchors.fill: parent
        color: "#0B1C22"
    }

    TapHandler {}

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 14
        visible: root.hasNode

        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            TrackGlyph {
                track: root.node.track || ""
                ink: root.accent
                Layout.preferredWidth: 26
                Layout.preferredHeight: 26
            }
            MapText {
                Layout.fillWidth: true
                text: root.node.title || ""
                color: "#F2FFFB"
                font.pixelSize: 28
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Rectangle {
                visible: Boolean(root.node.stage)
                width: stageTag.implicitWidth + 16
                height: 28
                radius: 14
                color: "#2A4A52"
                MapText {
                    id: stageTag
                    anchors.centerIn: parent
                    text: polaris.stageBadge(root.node.stage || "")
                    color: polaris.stageColor(root.node.stage || "")
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }
            }
            PriorityMeter { priority: root.node.priority || ""; lamp: 12 }
            MapText {
                text: "Esc"
                color: escHover.hovered ? "#E8F7F2" : "#8FB9AE"
                font.pixelSize: 13
                HoverHandler { id: escHover }
                TapHandler { onTapped: root.closed() }
            }
        }

        MapText {
            Layout.fillWidth: true
            text: polaris.priorityLabel(root.node.priority || "")
                + " · " + polaris.volatilityLabel(root.node.volatility || "")
                + " · " + polaris.validationLabel(root.node.validation || "")
            color: polaris.priorityColor(root.node.priority || "")
            font.pixelSize: 14
            wrapMode: Text.WordWrap
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: width
            contentHeight: pageColumn.height
            ScrollBar.vertical: ScrollBar { }

            Column {
                id: pageColumn
                width: parent.width
                spacing: 18

                CourseIntro {
                    width: parent.width
                    node: root.node
                    extras: true
                    headingSize: 16
                    bodySize: 17
                }

                Column {
                    visible: root.inbound.length > 0
                    width: parent.width
                    spacing: 8
                    MapText {
                        text: "先修与来路"
                        color: "#9AD7C8"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.inbound
                        delegate: Column {
                            required property var modelData
                            width: pageColumn.width
                            spacing: 4
                            MapText {
                                width: parent.width
                                text: (modelData.strong ? "门槛：" : "来路：")
                                      + (modelData.title || "")
                                      + (modelData.strong ? "" : " · 知道渊源会更透彻，不是入学条件")
                                color: linkIn.hovered ? "#C6F4E8" : "#7EF0D4"
                                font.pixelSize: 16
                                font.underline: linkIn.hovered
                                wrapMode: Text.WordWrap
                                HoverHandler { id: linkIn }
                                TapHandler { onTapped: polaris.openNode(modelData.id) }
                            }
                            MapText {
                                visible: Boolean(modelData.rationale)
                                width: parent.width
                                text: modelData.rationale || ""
                                color: "#D5EBE6"
                                font.pixelSize: 16
                                wrapMode: Text.WordWrap
                                lineHeight: 1.34
                                lineHeightMode: Text.ProportionalHeight
                            }
                        }
                    }
                }

                Column {
                    visible: root.outbound.length > 0
                    width: parent.width
                    spacing: 8
                    MapText {
                        text: "它为谁铺路"
                        color: "#9AD7C8"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.outbound
                        delegate: Column {
                            required property var modelData
                            width: pageColumn.width
                            spacing: 4
                            MapText {
                                width: parent.width
                                text: (modelData.strong ? "门槛：" : "来路：")
                                      + (modelData.title || "")
                                color: linkOut.hovered ? "#C6F4E8" : "#7EF0D4"
                                font.pixelSize: 16
                                font.underline: linkOut.hovered
                                wrapMode: Text.WordWrap
                                HoverHandler { id: linkOut }
                                TapHandler { onTapped: polaris.openNode(modelData.id) }
                            }
                            MapText {
                                visible: Boolean(modelData.rationale)
                                width: parent.width
                                text: modelData.rationale || ""
                                color: "#D5EBE6"
                                font.pixelSize: 16
                                wrapMode: Text.WordWrap
                                lineHeight: 1.34
                                lineHeightMode: Text.ProportionalHeight
                            }
                        }
                    }
                }

                Rectangle {
                    visible: Boolean(root.node.priority_reason || root.node.stage_reason)
                    width: parent.width
                    height: necessityColumn.implicitHeight + 24
                    radius: 18
                    color: "#3315262C"
                    border.color: "#C45C2A"
                    Column {
                        id: necessityColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 14
                        spacing: 8
                        MapText {
                            text: "必要性"
                            color: "#FFD2B0"
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                        MapText {
                            visible: Boolean(root.node.priority_reason)
                            width: parent.width
                            text: root.node.priority_reason || ""
                            color: "#F2E6DC"
                            font.pixelSize: 16
                            wrapMode: Text.WordWrap
                            lineHeight: 1.32
                            lineHeightMode: Text.ProportionalHeight
                        }
                        MapText {
                            visible: Boolean(root.node.industry_reason)
                            width: parent.width
                            text: "军工里 · " + (root.node.industry_reason || "")
                            color: "#D7C4B4"
                            font.pixelSize: 15
                            wrapMode: Text.WordWrap
                            lineHeight: 1.28
                            lineHeightMode: Text.ProportionalHeight
                        }
                        MapText {
                            visible: Boolean(root.node.stage_reason)
                            width: parent.width
                            text: (polaris.stageBadge(root.node.stage || "") || "这一阶段")
                                  + " · " + (root.node.stage_reason || "")
                            color: "#A9C5C0"
                            font.pixelSize: 14
                            wrapMode: Text.WordWrap
                            lineHeight: 1.28
                            lineHeightMode: Text.ProportionalHeight
                        }
                    }
                }

                Rectangle {
                    visible: Boolean(root.node.chapters && root.node.chapters.length)
                    width: parent.width
                    height: chapterRoute.implicitHeight + 24
                    radius: 18
                    color: "#2215262C"
                    border.color: "#3D6F70"
                    ChapterRoute {
                        id: chapterRoute
                        anchors.fill: parent
                        anchors.margins: 12
                        chapters: root.node.chapters || []
                        accent: root.accent
                    }
                }

                Rectangle {
                    width: parent.width
                    height: 168
                    radius: 18
                    color: "#2215262C"
                    border.color: "#3D6F70"
                    NeighborGraph {
                        anchors.fill: parent
                        inbound: root.inbound
                        outbound: root.outbound
                        centerTitle: root.node.title || ""
                        accent: root.accent
                        onNodeOpened: function(nodeId) { polaris.openNode(nodeId) }
                    }
                }

                Column {
                    visible: Boolean(root.node.app)
                    width: parent.width
                    spacing: 6
                    MapText {
                        text: "下游应用"
                        color: "#9AD7C8"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    MapText {
                        width: parent.width
                        text: "这个领域由「" + (root.node.app || "") + "」应用承载，学习与练习在那里进行。"
                        color: "#A5F0DE"
                        font.pixelSize: 16
                        wrapMode: Text.WordWrap
                        lineHeight: 1.32
                    }
                }

                Column {
                    visible: root.crossLinks.length > 0
                    width: parent.width
                    spacing: 8
                    MapText {
                        text: "跨图关联"
                        color: "#9AD7C8"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.crossLinks
                        delegate: Column {
                            required property var modelData
                            width: pageColumn.width
                            spacing: 4
                            MapText {
                                width: parent.width
                                text: (modelData.incoming ? "前置：" : "它支撑：")
                                    + modelData.peer_title
                                    + "（" + modelData.map_title + "）"
                                    + (modelData.strong ? "" : " · 来路，非门槛")
                                color: crossHover.hovered ? "#C6F4E8" : "#7EF0D4"
                                font.pixelSize: 16
                                font.underline: crossHover.hovered
                                wrapMode: Text.WordWrap
                                HoverHandler { id: crossHover }
                                TapHandler {
                                    enabled: !root.mapIsLocked(modelData.map_id || "")
                                    onTapped: polaris.openNode(modelData.peer_id)
                                }
                            }
                            MapText {
                                width: parent.width
                                text: modelData.rationale || ""
                                color: "#B7CBC6"
                                font.pixelSize: 15
                                wrapMode: Text.WordWrap
                                lineHeight: 1.28
                            }
                        }
                    }
                }

                Column {
                    visible: Boolean(root.node.source_refs && root.node.source_refs.length)
                    width: parent.width
                    spacing: 6
                    MapText {
                        text: "来源"
                        color: "#9AD7C8"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Repeater {
                        model: root.node.source_refs || []
                        delegate: MapText {
                            required property var modelData
                            width: pageColumn.width
                            text: "• " + modelData.source_id + " · " + modelData.locator
                            color: "#A9C5C0"
                            font.pixelSize: 15
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
    }
}
