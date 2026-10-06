import QtQuick

// 地图会整体缩放。ClearType 是先栅格再拉伸，中文一放大缩小就发虚、变瘦、笔画断裂。
// 曲线光栅跟缩放走，字重和字面保持一块。
Text {
    font.family: uiFontFamily
    renderType: Text.CurveRendering
    renderTypeQuality: Text.VeryHighRenderTypeQuality
    antialiasing: true
}
