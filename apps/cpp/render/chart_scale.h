#pragma once

#include <vector>

using namespace std;

// 统计图表的配色。
//
// Cairo 取不到 GTK 的 @define-color 命名颜色，所以这里按十六进制集中定义、
// 并标注各自对应的 style.css 变量：改色时两边必须一起改，否则会出现图上
// 颜色和图例色块对不上的情况（"未开始"就这样漂移过一次）。
struct ChartColor {
    double r = 0;
    double g = 0;
    double b = 0;
};

constexpr ChartColor chart_color(unsigned int hex) {
    return {
        ((hex >> 16) & 0xFF) / 255.0,
        ((hex >> 8) & 0xFF) / 255.0,
        (hex & 0xFF) / 255.0};
}

inline constexpr ChartColor kChartMastered = chart_color(0x198754);    // @athena_success
inline constexpr ChartColor kChartInProgress = chart_color(0xfd7e14);  // @athena_orange
inline constexpr ChartColor kChartNotStarted = chart_color(0x9ea6ad);  // @athena_chart_neutral
inline constexpr ChartColor kChartLabelText = chart_color(0x212529);   // @athena_body_text
inline constexpr ChartColor kChartAxis = chart_color(0xced4da);        // @athena_border_strong
inline constexpr ChartColor kChartMutedText = chart_color(0x6c757d);   // @athena_muted

// 在两个颜色之间线性插值，t 会被夹到 [0, 1]。熟练度直方图用它表达
// "星级越高越偏绿、越低越偏橙"，不另外定义一套渐变色。
ChartColor mix_chart_color(const ChartColor& from, const ChartColor& to, double t);

// 计算"好看"的坐标轴刻度值：步长取 1/2/5 × 10^n，返回一组等距刻度，
// 首个不大于 min_value、末个不小于 max_value，因此坐标轴范围通常比
// [min_value, max_value] 略宽。
//
// target_count 是期望的刻度**段数**，不是精确值——实际返回的刻度个数由
// 选中的步长决定。target_count 小于 1 时按 1 处理；max_value 不大于
// min_value（含两者相等）时按一个宽度为 1 的区间处理，保证结果非空、
// 调用方不必单独判空。
vector<double> nice_ticks(double min_value, double max_value, int target_count);
