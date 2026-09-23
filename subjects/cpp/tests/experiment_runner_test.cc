#include "services/experiment_runner.h"

#include <glibmm/main.h>
#include <gtest/gtest.h>

#include <atomic>
#include <optional>

using namespace std;

TEST(ExperimentRunnerTest, RunsAndReturnsACompleteResult) {
    FunctionRegistry registry;
    registry.add("cpp.Sample.lesson", [](ostream& output) {
        output << "executed";
    });
    auto ui_alive = make_shared<atomic_bool>(true);
    ExperimentRunner runner(registry, ui_alive);

    auto loop = Glib::MainLoop::create();
    optional<ExperimentResult> completed;
    ASSERT_TRUE(runner.start(
        {.function_id = "cpp.Sample.lesson"},
        [&completed, &loop](const ExperimentResult& result) {
            completed = result;
            loop->quit();
        }));
    EXPECT_FALSE(runner.start({}, nullptr));
    loop->run();

    ASSERT_TRUE(completed.has_value());
    EXPECT_EQ(completed->output, "executed");
    EXPECT_NE(completed->display_output.find("耗时"), string::npos);
    EXPECT_FALSE(runner.running());
}
