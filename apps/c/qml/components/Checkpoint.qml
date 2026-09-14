import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// 对齐主程序 CheckpointView：多题小测、点选后给解析，不是讲解里的单次预测。
// 进度库还没接，只当场计分。每题必须能指出 source_refs。
Rectangle {
    id: root
    property string heading: "随堂考核"
    property string intro: ""
    property var questions: []

    readonly property int total: questions ? questions.length : 0
    property int index: 0
    property int picked: -1
    property bool revealed: false
    property int correctCount: 0
    property bool finished: false

    visible: total > 0
    color: "white"
    radius: 8
    border.color: "#dee2e6"
    implicitHeight: inner.implicitHeight + 28
    Layout.fillWidth: true

    onQuestionsChanged: restart()

    readonly property var current: {
        if (total === 0 || index < 0 || index >= total)
            return ({})
        return questions[index]
    }

    function cite(question) {
        const refs = (question && question.source_refs) || []
        const bits = []
        for (let i = 0; i < refs.length; ++i)
            bits.push(refs[i].id + " " + refs[i].loc)
        return bits.join(" · ")
    }

    function restart() {
        index = 0
        picked = -1
        revealed = false
        correctCount = 0
        finished = false
    }

    function submit() {
        if (picked < 0 || revealed || finished)
            return
        revealed = true
        if (picked === current.correct)
            correctCount += 1
    }

    function advance() {
        if (!revealed)
            return
        if (index + 1 >= total) {
            finished = true
            return
        }
        index += 1
        picked = -1
        revealed = false
    }

    ColumnLayout {
        id: inner
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 14
        spacing: 10

        Text {
            text: root.heading
            font.pointSize: 24
            font.bold: true
            color: "#052c65"
        }
        Text {
            visible: root.intro.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            color: "#495057"
            text: root.intro
        }

        Text {
            visible: !root.finished
            color: "#6c757d"
            text: "第 " + (root.index + 1) + " / " + root.total + " 题"
        }

        RowLayout {
            visible: !root.finished
            spacing: 10
            Text {
                color: curriculum.difficultyColor(root.current.difficulty || 0)
                text: "难度 " + (root.current.difficulty || "—")
            }
            Text {
                color: "#495057"
                text: curriculum.goalLabel(root.current.goal || "")
            }
        }

        Text {
            visible: !root.finished
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            font.bold: true
            color: "#212529"
            text: root.current.stem || ""
        }

        Repeater {
            model: root.finished ? [] : (root.current.choices || [])
            delegate: Button {
                required property int index
                required property var modelData
                Layout.fillWidth: true
                text: modelData
                enabled: !root.revealed
                highlighted: root.picked === index
                onClicked: root.picked = index
            }
        }

        Rectangle {
            visible: root.revealed && !root.finished
            Layout.fillWidth: true
            color: root.picked === root.current.correct ? "#d1e7dd" : "#f8d7da"
            radius: 8
            implicitHeight: feedbackCol.height + 20
            Column {
                id: feedbackCol
                x: 12
                y: 10
                width: parent.width - 24
                spacing: 6
                Text {
                    text: root.picked === root.current.correct ? "对" : "不对"
                    font.bold: true
                    color: root.picked === root.current.correct ? "#0f5132" : "#842029"
                }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    text: root.current.explain || ""
                    color: "#212529"
                }
                Text {
                    width: parent.width
                    wrapMode: Text.WordWrap
                    color: "#6c757d"
                    text: "依据：" + root.cite(root.current)
                }
            }
        }

        RowLayout {
            visible: !root.finished
            Button {
                text: "提交"
                enabled: root.picked >= 0 && !root.revealed
                highlighted: true
                onClicked: root.submit()
            }
            Button {
                visible: root.revealed
                text: root.index + 1 >= root.total ? "看成绩" : "下一题"
                onClicked: root.advance()
            }
        }

        ColumnLayout {
            visible: root.finished
            spacing: 8
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                font.bold: true
                color: "#052c65"
                text: "答对 " + root.correctCount + " / " + root.total
                      + "。进度还没落库，这只是当场核对。"
            }
            Button {
                text: "再做一遍"
                onClicked: root.restart()
            }
        }
    }
}
