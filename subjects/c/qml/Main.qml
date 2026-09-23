import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "pages" as Pages

ApplicationWindow {
    id: win
    visible: true
    width: 1440
    height: 900
    minimumWidth: 960
    minimumHeight: 640
    title: "C 语言编程"
    color: "#f8f9fa"
    font.pointSize: 22

    header: Rectangle {
        height: 120
        color: "white"
        border.color: "#dee2e6"
        border.width: 1

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 22
            anchors.rightMargin: 22
            spacing: 12

            Button {
                visible: curriculum.pageIndex !== 0
                text: "知识图谱"
                onClicked: curriculum.goHome()
            }
            Button {
                visible: curriculum.pageIndex === 2
                text: "本章大纲"
                onClicked: curriculum.openOutline()
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Text {
                    text: curriculum.pageIndex === 2
                          ? curriculum.selectedTopic.title
                          : curriculum.pageIndex === 1
                            ? (curriculum.chapter.title || "教学大纲")
                            : curriculum.title
                    font.pointSize: 28
                    font.bold: true
                    color: "#052c65"
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: curriculum.pageIndex === 2
                          ? (curriculum.selectedTopic.description || "")
                          : curriculum.pageIndex === 1
                            ? (curriculum.chapter.summary || "")
                            : curriculum.tagline
                    color: "#495057"
                }
            }

            Button {
                text: "实验台"
                highlighted: true
                onClicked: curriculum.launchLab()
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Text {
            visible: curriculum.error.length > 0 || curriculum.labMessage.length > 0
            Layout.fillWidth: true
            Layout.leftMargin: 20
            Layout.topMargin: 8
            color: "#b02a37"
            text: curriculum.error || curriculum.labMessage
            wrapMode: Text.WordWrap
        }

        Text {
            visible: curriculum.pageIndex === 0
            Layout.fillWidth: true
            Layout.leftMargin: 24
            Layout.topMargin: 10
            color: "#6c757d"
            text: "每一张卡片是一章，层是章与章的先修。点卡片进入该章大纲；教案只能从章内知识点路线图点进来。灰章是规划中，仍可点进去看方向。"
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: curriculum.pageIndex

            Pages.GraphPage {}
            Pages.OutlinePage {}
            Loader {
                source: curriculum.lessonSource
                onStatusChanged: {
                    if (status === Loader.Error)
                        console.warn("教案加载失败：", source)
                }
            }
        }
    }
}
