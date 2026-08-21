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
