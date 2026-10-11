#include "render/chart_scale.h"

#include <gtest/gtest.h>

#include <cmath>

namespace {

// 刻度是要当文本显示的，浮点误差会直接变成 "0.30000000000000004" 这种
// 标签，所以比较时容差取得很小。
constexpr double kEpsilon = 1e-9;

void ExpectTicks(
    const vector<double>& actual,
    const vector<double>& expected) {
    ASSERT_EQ(actual.size(), expected.size());
    for (size_t index = 0; index < expected.size(); ++index) {
        EXPECT_NEAR(actual[index], expected[index], kEpsilon)
            << "刻度下标 " << index;
    }
}

TEST(ChartScaleTest, PicksRoundStepsForCommonRanges) {
    // 0-1 的比例轴要 4 段的话，原始步长 0.25 不在 1/2/5 步长族里，会被
    // 归整到 0.5——所以百分比轴应该按 5 段要，才能拿到 20% 一档的网格线。
    ExpectTicks(nice_ticks(0, 1, 4), {0, 0.5, 1.0});
    ExpectTicks(nice_ticks(0, 1, 5), {0, 0.2, 0.4, 0.6, 0.8, 1.0});
    // 0-7 -> 原始步长 1.75，归整到 2。
    ExpectTicks(nice_ticks(0, 7, 4), {0, 2, 4, 6, 8});
    // 0-71（当前 cpp 知识点总数量级）-> 步长 20。
    ExpectTicks(nice_ticks(0, 71, 4), {0, 20, 40, 60, 80});
}

TEST(ChartScaleTest, RangeCoversRequestedValues) {
    const auto ticks = nice_ticks(0, 13, 4);
    ASSERT_FALSE(ticks.empty());
    EXPECT_LE(ticks.front(), 0.0);
    EXPECT_GE(ticks.back(), 13.0);
}

// 直方图在没有任何数据时 peak 是 0，轴的上界会被拿去做除数；退化区间必须
// 返回可用刻度，否则要么除零、要么图上一条线都没有。
TEST(ChartScaleTest, DegenerateRangesStillProduceUsableTicks) {
    const auto zero_range = nice_ticks(0, 0, 4);
    ASSERT_GE(zero_range.size(), 2u);
    EXPECT_NEAR(zero_range.front(), 0.0, kEpsilon);
    EXPECT_GT(zero_range.back(), 0.0);

    // 上界小于下界同样按宽度 1 处理，不返回空。
    EXPECT_FALSE(nice_ticks(5, 1, 4).empty());
    // 期望段数非法时按 1 段处理。
    EXPECT_FALSE(nice_ticks(0, 10, 0).empty());
    EXPECT_FALSE(nice_ticks(0, 10, -3).empty());
}

TEST(ChartScaleTest, TicksAreExactlyRepresentableForLabels) {
    // 0.1 步长最容易暴露累加误差：逐个乘回步长后应当没有长尾小数。
    const auto ticks = nice_ticks(0, 0.5, 5);
    for (const double tick : ticks) {
        const double scaled = tick * 10.0;
        EXPECT_NEAR(scaled, round(scaled), kEpsilon) << "刻度 " << tick;
    }
}

TEST(ChartScaleTest, MixClampsAndInterpolatesEndpoints) {
    const ChartColor from = chart_color(0x000000);
    const ChartColor to = chart_color(0xffffff);

    const ChartColor start = mix_chart_color(from, to, 0.0);
    EXPECT_NEAR(start.r, 0.0, kEpsilon);

    const ChartColor end = mix_chart_color(from, to, 1.0);
    EXPECT_NEAR(end.r, 1.0, kEpsilon);

    const ChartColor middle = mix_chart_color(from, to, 0.5);
    EXPECT_NEAR(middle.r, 0.5, kEpsilon);

    // 越界的 t 不应该算出超出色域的分量。
    EXPECT_NEAR(mix_chart_color(from, to, -2.0).r, 0.0, kEpsilon);
    EXPECT_NEAR(mix_chart_color(from, to, 9.0).r, 1.0, kEpsilon);
}

TEST(ChartScaleTest, ChartColorDecodesHex) {
    const ChartColor success = chart_color(0x198754);
    EXPECT_NEAR(success.r, 0x19 / 255.0, kEpsilon);
    EXPECT_NEAR(success.g, 0x87 / 255.0, kEpsilon);
    EXPECT_NEAR(success.b, 0x54 / 255.0, kEpsilon);
}

} // namespace
