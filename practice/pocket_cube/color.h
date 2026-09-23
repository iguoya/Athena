#pragma once

// 十六进制颜色转 Cairo 用的 0-1 浮点 RGB。从 subjects/cpp 的 render/chart_scale.h
// 抄一份最小子集过来，不 include 那边的头文件——应用之间不互相引用路径
// （主仓库 AGENTS.md「构建完全隔离」）。那边的 nice_ticks()/mix_chart_color()
// 是图表专属的，这里用不上，不搬。

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
