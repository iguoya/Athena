#include "render/chart_scale.h"

#include <algorithm>
#include <cmath>

ChartColor mix_chart_color(
    const ChartColor& from,
    const ChartColor& to,
    double t) {
    const double ratio = clamp(t, 0.0, 1.0);
    const auto mix = [ratio](double a, double b) { return a + (b - a) * ratio; };
    return {mix(from.r, to.r), mix(from.g, to.g), mix(from.b, to.b)};
}

vector<double> nice_ticks(double min_value, double max_value, int target_count) {
    const int segments = max(target_count, 1);
    // 退化区间（上界不大于下界、或者传进来 NaN）统一按宽度 1 处理，
    // 让调用方总能拿到至少两个刻度，不必单独判空。
    if (!(max_value > min_value)) {
        max_value = min_value + 1.0;
    }

    const double raw_step = (max_value - min_value) / segments;
    const double magnitude = pow(10.0, floor(log10(raw_step)));
    const double normalized = raw_step / magnitude;
    double step = 10.0;
    if (normalized <= 1.0) {
        step = 1.0;
    } else if (normalized <= 2.0) {
        step = 2.0;
    } else if (normalized <= 5.0) {
        step = 5.0;
    }
    step *= magnitude;

    const double first = floor(min_value / step) * step;
    const double last = ceil(max_value / step) * step;

    vector<double> ticks;
    // 用整数计数推进而不是反复累加 step，避免浮点误差累积导致多出或少掉
    // 一个刻度。
    const int count = static_cast<int>(lround((last - first) / step));
    ticks.reserve(static_cast<size_t>(count) + 1);
    for (int index = 0; index <= count; ++index) {
        double tick = first + step * index;
        // 步长是 1/2/5 × 10^n，浮点乘法可能算出 -0 或 0.30000000000000004
        // 这类值；刻度要当文本显示，这里按步长的量级归整一次。
        tick = round(tick / step) * step;
        ticks.push_back(tick == 0.0 ? 0.0 : tick);
    }
    return ticks;
}
