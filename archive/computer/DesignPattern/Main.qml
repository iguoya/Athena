import QtQuick
import QtQuick.Controls 6.5
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    width: 800
    height: 600
    title: qsTr("Tree Menu Example")

    // 定义视图组件
    Component {
        id: homeView
        Rectangle {
            width: parent.width
            height: parent.height
            color: "lightblue"
            Text {
                anchors.centerIn: parent
                text: "Home Content"
            }
        }
    }

    Component {
        id: profileView
        Rectangle {
            width: parent.width
            height: parent.height
            color: "lightgreen"
            Text {
                anchors.centerIn: parent
                text: "Profile Content"
            }
        }
    }

    Component {
        id: settingsView
        Rectangle {
            width: parent.width
            height: parent.height
            color: "lightyellow"
            Text {
                anchors.centerIn: parent
                text: "Settings Content"
            }
        }
    }

    Component {
        id: helpView
        Rectangle {
            width: parent.width
            height: parent.height
            color: "lightcoral"
            Text {
                anchors.centerIn: parent
                text: "Help Content"
            }
        }
    }

    // 定义菜单模型
    ListModel {
        id: menuModel
        ListElement { name: "Home"; view: "homeView" }
        ListElement { name: "Profile"; view: "profileView" }
        ListElement { name: "Settings"; view: "settingsView" }
        ListElement { name: "Help"; view: "helpView" }
    }

    // 主布局
    RowLayout {
        anchors.fill: parent

        // 左侧树形菜单
        ListView {
            id: menuListView
            Layout.preferredWidth: 200
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
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
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
                        var viewComponent = contentViewComponent(model.view);
                        if (viewComponent) {
                            contentView.push(viewComponent.createObject(contentView));
                        }
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
        }
    }

    // 组件映射函数
    function contentViewComponent(viewName) {
        switch (viewName) {
            case "homeView":
                return homeView;
            case "profileView":
                return profileView;
            case "settingsView":
                return settingsView;
            case "helpView":
                return helpView;
            default:
                return null;
        }
    }
}
