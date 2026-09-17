import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components" as Atlas

ApplicationWindow {
    id: window
    visible: true
    width: 1640
    height: 980
    minimumWidth: 1180
    minimumHeight: 720
    title: atlas.title
    color: "#EEF1EE"
    font.pointSize: 18

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Atlas.MapIndex {
            Layout.fillHeight: true
            Layout.preferredWidth: 306
            maps: atlas.maps
            selectedMapId: atlas.selectedMapId
            onMapChosen: function(mapId) { atlas.openMap(mapId) }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#F7F5EE"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 18

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text {
                            text: atlas.selectedMapTitle || atlas.title
                            color: "#132B35"
                            font.pixelSize: 32
                            font.weight: Font.DemiBold
                        }
                        Text {
                            Layout.fillWidth: true
                            text: atlas.selectedMapSummary || atlas.subtitle
                            color: "#49606A"
                            wrapMode: Text.WordWrap
                            font.pixelSize: 17
                        }
                    }
                    Button {
                        text: "重置视图"
                        onClicked: routeMap.resetView()
                    }
                }

                Text {
                    visible: atlas.error.length > 0
                    Layout.fillWidth: true
                    color: "#A1202B"
                    text: atlas.error
                    wrapMode: Text.WordWrap
                }

                Atlas.RouteMap {
                    id: routeMap
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    nodes: atlas.nodes
                    edges: atlas.edges
                    canvasWidth: atlas.canvasWidth
                    canvasHeight: atlas.canvasHeight
                    selectedNodeId: atlas.selectedNode.id || ""
                    onNodeChosen: function(nodeId) { atlas.selectNode(nodeId) }
                    onBlankChosen: atlas.clearSelection()
                }

                Atlas.MapLegend {
                    Layout.fillWidth: true
                }
            }
        }

        Atlas.DetailPanel {
            Layout.fillHeight: true
            Layout.preferredWidth: 342
            node: atlas.selectedNode
            edges: atlas.edges
            onClosed: atlas.clearSelection()
        }
    }
}
