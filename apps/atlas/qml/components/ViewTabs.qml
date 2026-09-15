import QtQuick

// 体系 / 实操的视角切换（ADR 0008）。它们是同一个能力域的两个视角，不是两个对象，
// 所以用标签页而不是两个菜单项。
//
// 自绘而不用 QtQuick.Controls 的 TabBar：这套界面的配色是自定的（深色侧栏、米色
// 画布），标准控件的默认外观在里面很突兀。另一个原因是数据流——选中态一律由
// `family` 单向算出，点击只发信号，不在控件里存第二份状态。TabBar 的 currentIndex
// 是可写的，一旦点击就会打破绑定，之后要靠命令式代码往回同步。
Row {
    id: root

    // 当前视角，取值同 `family`：system / playbook。
    required property string family
    // 没有配对图时整块隐藏（不该出现一个点不动的标签页）。
    required property bool hasCompanion

    signal viewChosen(string family)

    spacing: 6
    visible: hasCompanion

    Repeater {
        model: [
            { label: "体系", family: "system" },
            { label: "实操", family: "playbook" }
        ]

        delegate: Rectangle {
            id: tab
            required property var modelData
            readonly property bool current: root.family === modelData.family

            implicitWidth: label.implicitWidth + 28
            height: 36
            radius: 9
            color: current ? "#316B78" : (hover.hovered ? "#E2E7DF" : "transparent")
            border.width: current ? 0 : 1
            border.color: "#CBD5CE"

            Text {
                id: label
                anchors.centerIn: parent
                text: tab.modelData.label
                color: tab.current ? "#FFFFFF" : "#49606A"
                font.pixelSize: 16
                font.weight: tab.current ? Font.DemiBold : Font.Medium
            }

            HoverHandler { id: hover }
            TapHandler {
                onTapped: {
                    if (!tab.current) {
                        root.viewChosen(tab.modelData.family)
                    }
                }
            }
        }
    }
}
