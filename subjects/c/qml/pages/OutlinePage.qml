import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components" as C

Flickable {
    contentWidth: width
    contentHeight: col.height + 48
    clip: true
    ScrollBar.vertical: ScrollBar {}

    readonly property var outline: curriculum.chapter.outline || {}

    ColumnLayout {
        id: col
        x: 28
        width: Math.min(parent.width - 56, 1100)
        spacing: 16

        Text {
            Layout.fillWidth: true
            text: outline.lead || ""
            wrapMode: Text.WordWrap
            font.pointSize: 26
            color: "#052c65"
            font.bold: true
        }
        Text {
            Layout.fillWidth: true
            text: outline.intro || ""
            wrapMode: Text.WordWrap
            color: "#212529"
        }
        Text {
            visible: (curriculum.chapter.source_refs || []).length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#6c757d"
            text: {
                const refs = curriculum.chapter.source_refs || []
                const bits = []
                for (let i = 0; i < refs.length; ++i)
                    bits.push(refs[i].source_id + " " + refs[i].locator)
                return "本有：" + bits.join(" · ")
            }
        }

        C.SectionFrame {
            Layout.fillWidth: true
            title: "先看主次与顺序"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: "箭头是本章知识点的先修。配色是难度；框里第二行是掌握目标。白卡片点进去学，灰卡片是规划中。"
            }
            C.TopicRoadmap {
                Layout.fillWidth: true
                Layout.preferredHeight: curriculum.topicGraphHeight
            }
            Repeater {
                model: outline.grades || []
                delegate: C.GradeGroup {
                    required property var modelData
                    Layout.fillWidth: true
                    goal: modelData.goal
                    label: modelData.label
                    note: modelData.note
                }
            }
        }

        C.SectionFrame {
            title: (outline.titles && outline.titles.origin) || "痛点与来历"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: outline.origin || ""
            }
        }
        C.SectionFrame {
            title: (outline.titles && outline.titles.model) || "心智模型"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: outline.model || ""
            }
        }
        C.SectionFrame {
            title: (outline.titles && outline.titles.scope) || "讲什么与边界"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: outline.scope || ""
            }
        }
        C.SectionFrame {
            title: (outline.titles && outline.titles.tradeoff) || "判断与代价"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: outline.tradeoff || ""
            }
        }
        C.SectionFrame {
            title: (outline.titles && outline.titles.landing) || "落点"
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#212529"
                text: outline.landing || ""
            }
        }
    }
}
