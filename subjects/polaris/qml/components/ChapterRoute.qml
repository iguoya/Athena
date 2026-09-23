import QtQuick
import QtQuick.Shapes

// 一门课自己的学习流程。实践与理论分成两种卡片：实践更醒目，
// 因为动手才能直接感到这门课为什么必要、能解决什么。
// 掌握度仍用 ACM CS2013：熟悉 / 运用 / 评估。
Item {
    id: root
    required property var chapters
    required property color accent
    property string selectedId: ""
    property string filter: ""

    readonly property var laidOut: root.layoutChapters(root.chapters || [])
    readonly property var selected: {
        const id = root.selectedId
        const nodes = root.laidOut.nodes
        for (let i = 0; i < nodes.length; ++i) {
            if (nodes[i].id === id)
                return nodes[i]
        }
        return null
    }

    implicitHeight: Math.max(240, laidOut.height + 88 + (selected ? 58 : 0))
    clip: true

    function isPractice(chapter) {
        if (chapter.kind === "practice" || chapter.hands_on === true)
            return true
        if (chapter.kind === "theory" || chapter.hands_on === false)
            return false
        return chapter.mastery === "usage" || chapter.mastery === "assessment"
    }

    function visibleInFilter(chapter) {
        if (!root.filter)
            return true
        if (root.filter === "practice")
            return root.isPractice(chapter)
        if (root.filter === "theory")
            return !root.isPractice(chapter)
        return (chapter.mastery || "") === root.filter
    }

    function layoutChapters(source) {
        const chapters = source || []
        if (chapters.length === 0)
            return { nodes: [], edges: [], width: 400, height: 120 }
        const indexOf = {}
        for (let i = 0; i < chapters.length; ++i)
            indexOf[chapters[i].id] = i
        const indeg = []
        const outgoing = []
        for (let i = 0; i < chapters.length; ++i) {
            indeg.push(0)
            outgoing.push([])
        }
        for (let i = 0; i < chapters.length; ++i) {
            const requires = chapters[i].requires || []
            for (let r = 0; r < requires.length; ++r) {
                const from = indexOf[requires[r]]
                if (from === undefined)
                    continue
                outgoing[from].push(i)
                indeg[i] += 1
            }
        }
        const layers = []
        let ready = []
        for (let i = 0; i < indeg.length; ++i) {
            if (indeg[i] === 0)
                ready.push(i)
        }
        const placed = {}
        while (ready.length > 0) {
            layers.push(ready.slice())
            const next = []
            for (let k = 0; k < ready.length; ++k) {
                const current = ready[k]
                placed[current] = true
                const outs = outgoing[current]
                for (let o = 0; o < outs.length; ++o) {
                    const target = outs[o]
                    indeg[target] -= 1
                    if (indeg[target] === 0)
                        next.push(target)
                }
            }
            ready = next
        }
        const leftover = []
        for (let i = 0; i < chapters.length; ++i) {
            if (!placed[i])
                leftover.push(i)
        }
        if (leftover.length > 0)
            layers.push(leftover)

        const cardW = 168
        const cardH = 86
        const gapX = 48
        const gapY = 14
        const pad = 14
        let tallest = 1
        for (let i = 0; i < layers.length; ++i)
            tallest = Math.max(tallest, layers[i].length)
        const height = pad * 2 + tallest * cardH + (tallest - 1) * gapY
        const width = pad * 2 + layers.length * cardW + Math.max(0, layers.length - 1) * gapX
        const nodes = []
        const byId = {}
        for (let li = 0; li < layers.length; ++li) {
            const layer = layers[li]
            const colH = layer.length * cardH + Math.max(0, layer.length - 1) * gapY
            let y = (height - colH) / 2
            const x = pad + li * (cardW + gapX)
            for (let n = 0; n < layer.length; ++n) {
                const src = chapters[layer[n]]
                const practice = root.isPractice(src)
                const node = {
                    id: src.id,
                    title: src.title,
                    summary: src.summary,
                    mastery: src.mastery || "usage",
                    requires: src.requires || [],
                    kind: practice ? "practice" : "theory",
                    hands_on: practice,
                    x: x,
                    y: y,
                    w: cardW,
                    h: cardH
                }
                nodes.push(node)
                byId[node.id] = node
                y += cardH + gapY
            }
        }
        const edges = []
        for (let i = 0; i < nodes.length; ++i) {
            const node = nodes[i]
            const requires = node.requires || []
            for (let r = 0; r < requires.length; ++r) {
                const from = byId[requires[r]]
                if (!from)
                    continue
                edges.push({
                    from: from.id,
                    to: node.id,
                    practice: node.hands_on && from.hands_on,
                    x0: from.x + from.w,
                    y0: from.y + from.h / 2,
                    x1: node.x,
                    y1: node.y + node.h / 2
                })
            }
        }
        return { nodes: nodes, edges: edges, width: width, height: height }
    }

    Column {
        anchors.fill: parent
        spacing: 8

        Row {
            spacing: 10
            MapText {
                text: "本课学习流程"
                color: "#9AD7C8"
                font.pixelSize: 14
                font.weight: Font.DemiBold
                anchors.verticalCenter: parent.verticalCenter
            }
            Repeater {
                model: [
                    { id: "practice", title: "实践", ink: "#C45C2A" },
                    { id: "theory", title: "理论", ink: "#6A7D84" },
                    { id: "", title: "全部", ink: "#2E8F7A" }
                ]
                delegate: Rectangle {
                    required property var modelData
                    height: 26
                    width: chipText.implicitWidth + 16
                    radius: 13
                    color: root.filter === modelData.id ? modelData.ink : "#1A3A40"
                    border.color: root.filter === modelData.id ? "#E7FFF7" : "#3D6F70"
                    MapText {
                        id: chipText
                        anchors.centerIn: parent
                        text: modelData.title
                        color: "#E8F7F2"
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                    }
                    TapHandler {
                        onTapped: root.filter = root.filter === modelData.id ? "" : modelData.id
                    }
                }
            }
            MapText {
                text: "熟悉 / 运用 / 评估"
                color: "#8FB4AD"
                font.pixelSize: 12
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        MapText {
            width: parent.width
            text: "实践用来直接感到这门课为什么必要；理论给实践一把尺子，不和动手抢视线。"
            color: "#A9C5C0"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }

        Flickable {
            width: parent.width
            height: root.laidOut.height + 8
            clip: true
            contentWidth: Math.max(width, root.laidOut.width + 8)
            contentHeight: height
            boundsBehavior: Flickable.StopAtBounds

            Item {
                width: root.laidOut.width
                height: root.laidOut.height

                Repeater {
                    model: root.laidOut.edges || []
                    delegate: Shape {
                        required property var modelData
                        anchors.fill: parent
                        preferredRendererType: Shape.CurveRenderer
                        antialiasing: true
                        opacity: {
                            const from = root.laidOut.nodes.find(function(n) { return n.id === modelData.from })
                            const to = root.laidOut.nodes.find(function(n) { return n.id === modelData.to })
                            if (!from || !to)
                                return 0.2
                            return (root.visibleInFilter(from) && root.visibleInFilter(to)) ? 1 : 0.1
                        }
                        ShapePath {
                            strokeColor: modelData.practice ? "#E08A4A" : "#6A8490"
                            strokeWidth: modelData.practice ? 2.4 : 1.2
                            fillColor: "transparent"
                            capStyle: ShapePath.RoundCap
                            dashPattern: modelData.practice ? [] : [5, 5]
                            startX: modelData.x0
                            startY: modelData.y0
                            PathCubic {
                                control1X: (modelData.x0 + modelData.x1) / 2
                                control1Y: modelData.y0
                                control2X: (modelData.x0 + modelData.x1) / 2
                                control2Y: modelData.y1
                                x: modelData.x1
                                y: modelData.y1
                            }
                        }
                    }
                }

                Repeater {
                    model: root.laidOut.nodes
                    delegate: Rectangle {
                        required property var modelData
                        readonly property bool practice: modelData.kind === "practice"
                        x: modelData.x
                        y: modelData.y
                        width: modelData.w
                        height: modelData.h
                        radius: practice ? 14 : 10
                        opacity: root.visibleInFilter(modelData) ? 1 : 0.18
                        color: {
                            if (root.selectedId === modelData.id)
                                return practice ? "#FFE7CC" : "#E8EEF0"
                            return practice ? "#FFF1E3" : "#D5DEE2"
                        }
                        border.color: practice ? "#E08A4A" : "#7A8F94"
                        border.width: practice ? 2 : 1
                        scale: practice ? 1 : 0.96

                        Rectangle {
                            visible: practice
                            anchors.centerIn: parent
                            width: parent.width + 18
                            height: parent.height + 18
                            radius: 18
                            color: "#E08A4A"
                            opacity: root.selectedId === modelData.id ? 0.28 : 0.12
                        }

                        Rectangle {
                            width: practice ? 8 : 4
                            height: parent.height
                            radius: 12
                            color: practice ? "#E08A4A" : "#7A8F94"
                        }

                        Column {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 8
                            anchors.topMargin: 8
                            anchors.bottomMargin: 8
                            spacing: 5
                            Row {
                                spacing: 6
                                Rectangle {
                                    height: 20
                                    width: kindText.implicitWidth + 12
                                    radius: 10
                                    color: practice ? "#C45C2A" : "#5C6B75"
                                    MapText {
                                        id: kindText
                                        anchors.centerIn: parent
                                        text: practice ? "实践" : "理论"
                                        color: "#FFF8F2"
                                        font.pixelSize: 12
                                        font.weight: Font.DemiBold
                                    }
                                }
                                Rectangle {
                                    height: 18
                                    width: gradeText.implicitWidth + 10
                                    radius: 9
                                    color: "transparent"
                                    border.color: polaris.chapterMasteryColor(modelData.mastery)
                                    MapText {
                                        id: gradeText
                                        anchors.centerIn: parent
                                        text: polaris.chapterMasteryLabel(modelData.mastery)
                                        color: polaris.chapterMasteryColor(modelData.mastery)
                                        font.pixelSize: 11
                                    }
                                }
                            }
                            MapText {
                                width: parent.width
                                text: modelData.title
                                color: "#132B32"
                                font.pixelSize: practice ? 14 : 13
                                font.weight: Font.DemiBold
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }
                        }
                        TapHandler {
                            onTapped: root.selectedId = modelData.id
                        }
                    }
                }
            }
        }

        MapText {
            visible: Boolean(root.selected)
            width: parent.width
            text: root.selected
                  ? ((root.selected.kind === "practice" ? "实践" : "理论")
                     + " · " + polaris.chapterMasteryLabel(root.selected.mastery)
                     + " · " + polaris.chapterMasteryHint(root.selected.mastery)
                     + "  "
                     + (root.selected.summary || ""))
                  : ""
            color: root.selected && root.selected.kind === "practice" ? "#FFD2B0" : "#D5EBE6"
            font.pixelSize: 14
            wrapMode: Text.WordWrap
            maximumLineCount: 3
            elide: Text.ElideRight
        }
    }
}
