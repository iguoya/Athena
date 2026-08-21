#pragma once

#include <functional>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

using namespace std;

struct AiChatResult {
    bool ok = false;
    string content;
    string error;
};

struct AiCredentials {
    string ark_api_key;
    string deepseek_api_key;
};

struct AiChatRequest {
    string endpoint;
    string model;
    string api_key;
    string prompt;
};

using AiTransport = function<AiChatResult(const AiChatRequest&)>;

struct AiQuizQuestion {
    string question;
    // 代码场景题的共享代码片段；为空时按普通文字题展示。
    string code;
    vector<string> options;
    vector<int> correct_indices;
    string explanation;
};

struct AiQuiz {
    vector<AiQuizQuestion> questions;
};

AiChatResult parse_ai_chat_response(string_view response_body);
string strip_markdown_code_fence(string_view text);
optional<AiQuiz> parse_ai_quiz_response(string_view response_body);

// 把一次完整自测的成绩换算为 0-5 星熟练度。按正确率向下取整，只有
// 全部答对才会得到 5 星；无有效题目时返回 0。
int mastery_from_quiz_score(int correct_answers, int total_questions);

class AiService final {
public:
    AiService();
    explicit AiService(AiTransport transport);

    // 优先使用火山方舟豆包；未配置或调用失败时回退 DeepSeek。
    AiChatResult chat(
        const AiCredentials& credentials,
        const string& prompt) const;

private:
    AiTransport m_transport;
};
