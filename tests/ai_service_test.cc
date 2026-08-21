#include "services/ai_service.h"

#include <glib.h>
#include <gtest/gtest.h>

#include <optional>
#include <stdexcept>

namespace {

class ScopedEnvironment final {
public:
    ScopedEnvironment(const string& name, const string& value)
        : m_name(name) {
        if (const char* current = g_getenv(m_name.c_str())) {
            m_original = current;
        }
        g_setenv(m_name.c_str(), value.c_str(), true);
    }

    ~ScopedEnvironment() {
        if (m_original) {
            g_setenv(m_name.c_str(), m_original->c_str(), true);
        } else {
            g_unsetenv(m_name.c_str());
        }
    }

private:
    string m_name;
    optional<string> m_original;
};

TEST(AiServiceTest, ParsesSuccessfulChatResponse) {
    const auto result = parse_ai_chat_response(
        R"({"choices":[{"message":{"content":"回答正文"}}]})");

    EXPECT_TRUE(result.ok);
    EXPECT_EQ(result.content, "回答正文");
    EXPECT_TRUE(result.error.empty());
}

TEST(AiServiceTest, ReportsProviderAndMalformedResponseErrors) {
    const auto provider_error = parse_ai_chat_response(
        R"({"error":{"message":"额度不足"}})");
    EXPECT_FALSE(provider_error.ok);
    EXPECT_EQ(provider_error.error, "额度不足");

    const auto malformed = parse_ai_chat_response("not json");
    EXPECT_FALSE(malformed.ok);
    EXPECT_NE(malformed.error.find("解析响应失败"), string::npos);
}

TEST(AiServiceTest, StripsOptionalMarkdownCodeFence) {
    EXPECT_EQ(strip_markdown_code_fence("  plain text  \n"), "plain text");
    EXPECT_EQ(
        strip_markdown_code_fence("```json\n{\"value\":1}\n```"),
        "{\"value\":1}\n");
}

TEST(AiServiceTest, ParsesAndNormalizesQuizQuestions) {
    const auto quiz = parse_ai_quiz_response(R"(
```json
{"questions":[
  {"question":"哪些下标有效？","options":["A","B","C"],
   "correct_indices":[2,-1,2,0,9],"explanation":"0 和 2"},
  {"question":"缺少正确答案","options":["A"],"correct_indices":[]},
  {"question":7,"options":["A"],"correct_indices":[0]}
]}
```
)");

    ASSERT_TRUE(quiz.has_value());
    ASSERT_EQ(quiz->questions.size(), 1u);
    EXPECT_EQ(quiz->questions[0].question, "哪些下标有效？");
    EXPECT_EQ(quiz->questions[0].options, (vector<string> {"A", "B", "C"}));
    EXPECT_EQ(quiz->questions[0].correct_indices, (vector<int> {0, 2}));
    EXPECT_EQ(quiz->questions[0].explanation, "0 和 2");
}

TEST(AiServiceTest, RejectsResponseWithoutUsableQuestions) {
    EXPECT_FALSE(parse_ai_quiz_response("not json").has_value());
    EXPECT_FALSE(parse_ai_quiz_response(R"({"questions":[]})").has_value());
    EXPECT_FALSE(parse_ai_quiz_response(R"({"questions":"wrong type"})").has_value());
}

TEST(AiServiceTest, ConvertsOnlyCompleteQuizResultsToFiveStars) {
    EXPECT_EQ(mastery_from_quiz_score(0, 0), 0);
    EXPECT_EQ(mastery_from_quiz_score(-1, 3), 0);
    EXPECT_EQ(mastery_from_quiz_score(0, 3), 0);
    EXPECT_EQ(mastery_from_quiz_score(1, 3), 1);
    EXPECT_EQ(mastery_from_quiz_score(2, 3), 3);
    EXPECT_EQ(mastery_from_quiz_score(3, 3), 5);
    EXPECT_EQ(mastery_from_quiz_score(8, 3), 5);
}

TEST(AiServiceTest, UsesArkFirstAndStopsAfterSuccess) {
    vector<AiChatRequest> requests;
    AiService service([&requests](const AiChatRequest& request) {
        requests.push_back(request);
        return AiChatResult {.ok = true, .content = "豆包回答"};
    });

    const auto result = service.chat(
        {.ark_api_key = "ark-key", .deepseek_api_key = "deepseek-key"},
        "测试提示词");

    ASSERT_TRUE(result.ok);
    ASSERT_EQ(requests.size(), 1u);
    EXPECT_EQ(requests[0].endpoint,
              "https://ark.cn-beijing.volces.com/api/v3/chat/completions");
    EXPECT_EQ(requests[0].model, "doubao-seed-2-1-pro-260628");
    EXPECT_EQ(requests[0].api_key, "ark-key");
    EXPECT_EQ(requests[0].prompt, "测试提示词");
}

TEST(AiServiceTest, FallsBackFromArkToDeepseek) {
    vector<AiChatRequest> requests;
    AiService service([&requests](const AiChatRequest& request) {
        requests.push_back(request);
        if (request.model == "doubao-seed-2-1-pro-260628") {
            return AiChatResult {.error = "豆包失败"};
        }
        return AiChatResult {.ok = true, .content = "DeepSeek 回答"};
    });

    const auto result = service.chat(
        {.ark_api_key = "ark-key", .deepseek_api_key = "deepseek-key"},
        "提示词");

    EXPECT_TRUE(result.ok);
    EXPECT_EQ(result.content, "DeepSeek 回答");
    ASSERT_EQ(requests.size(), 2u);
    EXPECT_EQ(requests[1].endpoint, "https://api.deepseek.com/chat/completions");
    EXPECT_EQ(requests[1].model, "deepseek-chat");
    EXPECT_EQ(requests[1].api_key, "deepseek-key");
}

TEST(AiServiceTest, SupportsDeepseekOnlyAndRejectsMissingKeys) {
    int call_count = 0;
    AiService service([&call_count](const AiChatRequest& request) {
        ++call_count;
        EXPECT_EQ(request.model, "deepseek-chat");
        return AiChatResult {.ok = true, .content = "回答"};
    });

    EXPECT_TRUE(service.chat({.deepseek_api_key = "key"}, "提示词").ok);
    EXPECT_EQ(call_count, 1);

    const auto missing = service.chat({}, "提示词");
    EXPECT_FALSE(missing.ok);
    EXPECT_NE(missing.error.find("未配置"), string::npos);
    EXPECT_EQ(call_count, 1);
}

TEST(AiServiceTest, RejectsEmptyTransport) {
    EXPECT_THROW(AiService(AiTransport {}), invalid_argument);
}

TEST(AiServiceTest, DefaultTransportIgnoresAnInvalidTmpDir) {
    const ScopedEnvironment invalid_tmpdir(
        "TMPDIR", "/path/that/does/not/exist");
    const ScopedEnvironment missing_curl("PATH", "/path/that/does/not/exist");

    const AiService service;
    const auto result =
        service.chat({.deepseek_api_key = "unused-test-key"}, "测试");

    EXPECT_FALSE(result.ok);
    EXPECT_NE(result.error.find("调用 curl 失败"), string::npos);
    EXPECT_EQ(result.error.find("无法创建临时请求文件"), string::npos);
}

} // namespace
