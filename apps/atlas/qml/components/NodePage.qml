import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Shapes

// 专页是仪器盘：邻域图画关系，三块表回答指南针，点表才展开原文。
Item {
    id: root
    required property var node
    signal closed()

    property int face: 0

    readonly property color accent: atlas.trackColor(root.node.track || "")
    readonly property var inbound: root.collect("to")
    readonly property var outbound: root.collect("from")
    readonly property var faces: [
        { title: "必要", tone: "#4AD4B2", body: root.node.priority_reason || "", hint: "为什么必须学" },
        { title: "能力", tone: "#7EB6E8", body: root.node.engineering_role || "", hint: "学完能做什么" },
        { title: "产出", tone: "#E0B36A", body: root.node.practice || "", hint: "能交出什么" }
    ]
    readonly property var currentFace: faces[Math.max(0, Math.min(2, face))]

    function collect(side) {
        const here = root.node.id || ""
        const list = []
        const edges = atlas.edges || []
        for (let i = 0; i < edges.length; ++i) {
            const edge = edges[i]
            if (side === "to" && edge.to === here)
                list.push({
                    id: edge.from,
                    title: atlas.nodeTitle(edge.from),
                    strong: edge.relation === "requires"
                })
            if (side === "from" && edge.from === here)
                list.push({
                    id: edge.to,
                    title: atlas.nodeTitle(edge.to),
                    strong: edge.relation === "requires"
                })
        }
        return list
    }

    function verifyMark() {
        const v = root.node.verify || ""
        if (v === "code") return "<>"
        if (v === "board") return "▣"
        if (v === "bench") return "∿"
        return "·"
    }

    function validationMark() {
        const v = root.node.validation || ""
        if (v === "measurement") return "测"
        if (v === "benchmark") return "比"
        if (v === "review") return "核"
        return "验"
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#F20B1C22" }
            GradientStop { position: 1.0; color: "#F5132B35" }
        }
    }

    Rectangle {
        width: 420
        height: 240
        radius: 180
        x: -100
        y: -80
        color: root.accent
        opacity: 0.22
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            Button { text: "返回图谱"; onClicked: root.closed() }
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
                elide: Text.ElideRight
            }
            PriorityMeter { priority: root.node.priority || ""; lamp: 12 }
            Rectangle {
                visible: Boolean(root.node.verify)
                width: verifyTag.implicitWidth + 14
                height: 26
                radius: 13
                color: "#35545C"
                MapText {
                    id: verifyTag
                    anchors.centerIn: parent
                    text: root.verifyMark() + "  " + atlas.verifyLabel(root.node.verify || "")
                    color: "#FFFFFF"
                    font.pixelSize: 12
                }
            }
            MapText { text: "Esc"; color: "#8FB9AE"; font.pixelSize: 13 }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 18

            NeighborGraph {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 720
                inbound: root.inbound
                outbound: root.outbound
                centerTitle: root.node.title || ""
                accent: root.accent
                onNodeOpened: function(nodeId) { atlas.openNode(nodeId) }
            }

            ColumnLayout {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: 400
                Layout.maximumWidth: 440
                spacing: 12

                Row {
                    Layout.fillWidth: true
                    spacing: 10
                    Repeater {
                        model: root.faces
                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            width: 118
                            height: 96
                            radius: 18
                            color: root.face === index ? "#442E8F7A" : "#2215262C"
                            border.color: modelData.tone
                            border.width: root.face === index ? 2 : 1
                            scale: faceHover.hovered ? 1.03 : 1
                            Behavior on scale { NumberAnimation { duration: 120 } }
                            Column {
                                anchors.centerIn: parent
                                spacing: 8
                                Rectangle {
                                    width: 42
                                    height: 42
                                    radius: 21
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    color: modelData.tone
                                    MapText {
                                        anchors.centerIn: parent
                                        text: index === 0 ? "衡" : (index === 1 ? "能" : "件")
                                        color: "#102026"
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                    }
                                }
                                MapText {
                                    text: modelData.title
                                    color: modelData.tone
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                    anchors.horizontalCenter: parent.horizontalCenter
                                }
                            }
                            HoverHandler { id: faceHover }
                            TapHandler { onTapped: root.face = index }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 72
                    radius: 16
                    color: "#2215262C"
                    border.color: "#3D6F70"
                    Row {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 18
                        Column {
                            spacing: 6
                            MapText { text: "先修"; color: "#8FB9AE"; font.pixelSize: 11 }
                            MapText {
                                text: String(root.inbound.length)
                                color: "#E8F7F2"
                                font.pixelSize: 26
                                font.weight: Font.DemiBold
                            }
                        }
                        Rectangle { width: 1; height: parent.height; color: "#3D6F70" }
                        Column {
                            spacing: 6
                            MapText { text: "下游"; color: "#8FB9AE"; font.pixelSize: 11 }
                            MapText {
                                text: String(root.outbound.length)
                                color: "#E8F7F2"
                                font.pixelSize: 26
                                font.weight: Font.DemiBold
                            }
                        }
                        Rectangle { width: 1; height: parent.height; color: "#3D6F70" }
                        Column {
                            spacing: 6
                            MapText { text: "验证"; color: "#8FB9AE"; font.pixelSize: 11 }
                            MapText {
                                text: root.validationMark()
                                color: "#E0B36A"
                                font.pixelSize: 26
                                font.weight: Font.DemiBold
                            }
                        }
                        Item { width: 8; height: 1 }
                        Column {
                            visible: Boolean(root.node.pitfall)
                            spacing: 6
                            MapText { text: "暗礁"; color: "#E0A090"; font.pixelSize: 11 }
                            Shape {
                                width: 28
                                height: 24
                                ShapePath {
                                    fillColor: "#E08A4A"
                                    strokeWidth: 0
                                    PathMove { x: 14; y: 2 }
                                    PathLine { x: 26; y: 22 }
                                    PathLine { x: 2; y: 22 }
                                    PathLine { x: 14; y: 2 }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 18
                    color: "#3315262C"
                    border.color: root.currentFace.tone
                    Column {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 8
                        MapText {
                            text: root.currentFace.hint
                            color: root.currentFace.tone
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                        }
                        Flickable {
                            width: parent.width
                            height: parent.height - 28
                            clip: true
                            contentWidth: width
                            contentHeight: faceBody.height
                            MapText {
                                id: faceBody
                                width: parent.width
                                text: root.currentFace.body
                                color: "#E7F4F0"
                                font.pixelSize: 16
                                wrapMode: Text.WordWrap
                                lineHeight: 1.32
                                lineHeightMode: Text.ProportionalHeight
                            }
                        }
                    }
                }

                Rectangle {
                    visible: Boolean(root.node.app)
                    Layout.fillWidth: true
                    height: 40
                    radius: 12
                    color: "#332E8F7A"
                    MapText {
                        anchors.centerIn: parent
                        text: "细节由下游应用承接  ·  " + root.node.app
                        color: "#A5F0DE"
                        font.pixelSize: 13
                    }
                }
            }
        }
    }
}
