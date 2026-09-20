import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components" as Atlas

ApplicationWindow {
    id: window
    visible: true
    width: 1720
    height: 1020
    minimumWidth: 1180
    minimumHeight: 720
    title: atlas.title
    color: "#07151A"
    font.family: uiFontFamily
    font.pointSize: 16
    font.weight: Font.Medium

    property bool nodePageOpen: false

    function mapIsLocked(mapId) {
        const maps = atlas.maps
        for (let i = 0; i < maps.length; ++i) {
            if (maps[i].id === mapId)
                return maps[i].view_kind !== "academic"
        }
        return true
    }

    function openMap(mapId) {
        if (window.mapIsLocked(mapId))
            return
        window.nodePageOpen = false
        atlas.openMap(mapId)
        routeMap.clearInspect()
        routeMap.resetView()
    }

    function enterNode(nodeId) {
        atlas.openNode(nodeId)
        window.nodePageOpen = true
    }

    function returnToMap() {
        window.nodePageOpen = false
    }

    Shortcut {
        sequences: [ StandardKey.Cancel, "Escape" ]
        onActivated: {
            if (theoryPopup.opened) {
                theoryPopup.close()
                return
            }
            if (window.nodePageOpen) {
                window.returnToMap()
                return
            }
            if (routeMap.inspectedEdge) {
                routeMap.inspectedEdge = null
                return
            }
            atlas.clearSelection()
            routeMap.clearInspect()
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Atlas.MapIndex {
            Layout.fillHeight: true
            Layout.preferredWidth: 336
            maps: atlas.maps
            selectedMapId: atlas.selectedMapId
            mapNodes: atlas.nodes
            selectedNodeId: atlas.selectedNode.id || ""
            onMapChosen: function(mapId) { window.openMap(mapId) }
            onNodeChosen: function(nodeId) { window.enterNode(nodeId) }
            onNodeHovered: function(nodeId) {
                if (!window.nodePageOpen)
                    routeMap.hoveredNodeId = nodeId
            }
        }

        Item {
            id: stage
            Layout.fillWidth: true
            Layout.fillHeight: true

            Atlas.RouteMap {
                id: routeMap
                anchors.fill: parent
                nodes: atlas.nodes
                edges: atlas.edges
                canvasWidth: atlas.canvasWidth
                canvasHeight: atlas.canvasHeight
                selectedNodeId: atlas.selectedNode.id || ""
                opacity: window.nodePageOpen ? 0.18 : 1
                Behavior on opacity { NumberAnimation { duration: 320; easing.type: Easing.OutCubic } }
                onNodeChosen: function(nodeId) {
                    atlas.selectNode(nodeId)
                    routeMap.flyTo(nodeId)
                }
                onNodeOpened: function(nodeId) { window.enterNode(nodeId) }
                onBlankChosen: {
                    if (!window.nodePageOpen)
                        atlas.clearSelection()
                }
            }

            Atlas.MapHud {
                id: hud
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.margins: 16
                visible: !window.nodePageOpen
                nodes: atlas.nodes
                theory: atlas.selectedMapTheory
                layerFilter: routeMap.layerFilter
                onLayerChosen: function(layerId) {
                    routeMap.layerFilter = routeMap.layerFilter === layerId ? "" : layerId
                }
                onTheoryChosen: function(item) {
                    theoryPopup.item = item
                    theoryPopup.open()
                }
            }

            Atlas.EdgeCallout {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: hud.top
                anchors.bottomMargin: 12
                visible: !window.nodePageOpen && Boolean(routeMap.inspectedEdge)
                edge: routeMap.inspectedEdge
            }

            Atlas.NodePage {
                id: nodePage
                anchors.fill: parent
                node: atlas.selectedNode
                opacity: window.nodePageOpen ? 1 : 0
                visible: opacity > 0.01
                Behavior on opacity { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
                onClosed: window.returnToMap()
            }
        }
    }

    Popup {
        id: theoryPopup
        property var item: ({})
        anchors.centerIn: parent
        width: Math.min(520, window.width - 80)
        modal: true
        dim: true
        padding: 24
        background: Rectangle {
            radius: 18
            color: "#F4FBFA"
            border.color: "#4AD4B2"
        }
        Column {
            width: parent.width
            spacing: 10
            Text {
                text: "理论科目 · 不建节点"
                color: "#147A5C"
                font.pixelSize: 13
                font.weight: Font.DemiBold
            }
            Text {
                width: parent.width
                text: theoryPopup.item && theoryPopup.item.name ? theoryPopup.item.name : ""
                color: "#132B32"
                font.pixelSize: 22
                font.weight: Font.DemiBold
                wrapMode: Text.WordWrap
            }
            Text {
                width: parent.width
                text: theoryPopup.item && theoryPopup.item.content ? theoryPopup.item.content : ""
                color: "#40545B"
                font.pixelSize: 16
                wrapMode: Text.WordWrap
            }
            Text {
                width: parent.width
                text: theoryPopup.item && theoryPopup.item.role ? ("起什么作用：" + theoryPopup.item.role) : ""
                color: "#5A6D72"
                font.pixelSize: 15
                wrapMode: Text.WordWrap
            }
        }
    }
}
