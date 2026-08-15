import QtQuick 6.4
import QtQuick.Controls 6.4
import QtQuick.Layouts 6.4

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: qsTr("Left Menu Example")

    // 左侧菜单宽度
    property int menuWidth: 200

    // 菜单项数据模型
    ListModel {
        id: menuModel
        ListElement { name: "Home" }
        ListElement { name: "Profile" }
        ListElement { name: "Settings" }
        ListElement { name: "Help" }
    }

    // 主布局
    RowLayout {
        anchors.fill: parent

        // 左侧菜单
        ListView {
            id: menuListView
            width: menuWidth
            Layout.fillHeight: true
            model: menuModel
            delegate: Item {
                width: menuListView.width
                height: 50
                RowLayout {
                    anchors.fill: parent
                    spacing: 10

                    Rectangle {
                        width: 20
                        height: 50
                        color: "transparent"
                    }

                    Text {
                        text: model.name
                        font.pixelSize: 20
                        anchors.verticalCenter: parent.verticalCenter
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        width: menuListView.width - 40
                    }

                    Rectangle {
                        width: 20
                        height: 50
                        color: "transparent"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        contentView.currentIndex = index
                    }
                }
            }
        }

        // 主内容区域
        StackView {
            id: contentView
            Layout.fillWidth: true
            Layout.fillHeight: true
            initialItem: Rectangle {
                width: parent.width
                height: parent.height
                color: "lightgray"
                Text {
                    anchors.centerIn: parent
                    text: "请选择一个菜单"
                }
            }

            Repeater {
                model: menuModel

                Rectangle {
                    width: parent.width
                    height: parent.height
                    color: "white"

                    Text {
                        anchors.centerIn: parent
                        text: model.name
                    }
                }
            }
        }
    }
}
