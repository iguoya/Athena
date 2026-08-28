#include "services/experiment_runner.h"

#include <glibmm/main.h>
#include <gtest/gtest.h>

#include <atomic>
#include <filesystem>
#include <fstream>
#include <optional>

using namespace std;

TEST(ExperimentRunnerTest, RunsAndPersistsACompleteResult) {
    const auto temporary_root = filesystem::temp_directory_path()
        / "athena-experiment-runner-test";
    filesystem::create_directories(temporary_root / "language");
    {
        ofstream source(temporary_root / "language" / "sample.hpp");
        source << "class Sample {\npublic:\n"
                  "    void lesson(ostream& output) const {\n"
                  "        output << \"source\";\n"
                  "    }\n};\n";
    }

    ContentLoader loader(temporary_root.string());
    FunctionRegistry registry;
    registry.add("cpp.Sample.lesson", [](ostream& output) {
        output << "executed";
    });
    LearningStore store(":memory:");
    auto ui_alive = make_shared<atomic_bool>(true);
    ExperimentRunner runner(
        registry, loader, &store, temporary_root.string(), ui_alive);

    auto loop = Glib::MainLoop::create();
    optional<ExperimentResult> completed;
    ASSERT_TRUE(runner.start(
        {.function_id = "cpp.Sample.lesson",
         .source_path = "language/sample.hpp",
         .member_name = "lesson"},
        [&completed, &loop](const ExperimentResult& result) {
            completed = result;
            loop->quit();
        }));
    EXPECT_FALSE(runner.start({}, nullptr));
    loop->run();

    ASSERT_TRUE(completed.has_value());
    EXPECT_EQ(completed->output, "executed");
    EXPECT_NE(completed->display_output.find("耗时"), string::npos);
    EXPECT_NE(completed->source_snapshot.find("void lesson"), string::npos);
    EXPECT_FALSE(runner.running());

    const auto runs = store.recent_runs("cpp.Sample.lesson", 5);
    ASSERT_EQ(runs.size(), 1U);
    EXPECT_EQ(runs.front().output, "executed");
    EXPECT_EQ(runs.front().source_snapshot, completed->source_snapshot);

    filesystem::remove_all(temporary_root);
}
