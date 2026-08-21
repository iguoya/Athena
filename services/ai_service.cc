#include "ai_service.h"

#include <glib.h>
#include <glib/gstdio.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>
#include <unistd.h>

namespace {

using json = nlohmann::json;

constexpr const char* kArkEndpoint =
    "https://ark.cn-beijing.volces.com/api/v3/chat/completions";
constexpr const char* kArkModel = "doubao-seed-2-1-pro-260628";
constexpr const char* kDeepseekEndpoint =
    "https://api.deepseek.com/chat/completions";
constexpr const char* kDeepseekModel = "deepseek-chat";

string shell_quote(const string& value) {
    gchar* quoted = g_shell_quote(value.c_str());
    const string result = quoted ? quoted : "";
    g_free(quoted);
    return result;
}

string write_secure_temp_file(const string& name_template, const string& content) {
    gchar* path_raw = nullptr;
    const gint fd = g_file_open_tmp(name_template.c_str(), &path_raw, nullptr);
    if (fd < 0) {
        g_free(path_raw);
        return "";
    }
    close(fd);
    const string path = path_raw;
    g_free(path_raw);

    ofstream stream(path, ios::binary);
    stream << content;
    stream.close();
    if (!stream) {
        g_remove(path.c_str());
        return "";
    }
    return path;
}

AiChatResult perform_ai_request(const AiChatRequest& request) {
    const json request_body = {
        {"model", request.model},
        {"messages",
         json::array({{{"role", "user"}, {"content", request.prompt}}})},
        {"stream", false},
    };

    const string config_path = write_secure_temp_file(
        "athena-ai-chat-XXXXXX.cfg",
        "header = \"Authorization: Bearer " + request.api_key + "\"\n"
        "header = \"Content-Type: application/json\"\n");
    const string body_path = write_secure_temp_file(
        "athena-ai-chat-XXXXXX.json", request_body.dump());

    struct TempFileGuard {
        vector<string> paths;
        ~TempFileGuard() {
            for (const auto& path : paths) {
                if (!path.empty()) {
                    g_remove(path.c_str());
                }
            }
        }
    } guard {{config_path, body_path}};

    if (config_path.empty() || body_path.empty()) {
        return {.error = "无法创建临时请求文件"};
    }

    const string command = "curl -sS --max-time 30 --connect-timeout 10 -K "
        + shell_quote(config_path) + " --data @" + shell_quote(body_path)
        + " " + shell_quote(request.endpoint);
    gchar* output_raw = nullptr;
    gint exit_status = 0;
    GError* spawn_error = nullptr;
    const gboolean spawned = g_spawn_command_line_sync(
        command.c_str(),
        &output_raw,
        nullptr,
        &exit_status,
        &spawn_error);
    const string response_body = output_raw ? output_raw : "";
    g_free(output_raw);

    if (!spawned) {
        const string message = spawn_error ? spawn_error->message : "未知错误";
        g_clear_error(&spawn_error);
        return {.error = "调用 curl 失败：" + message};
    }
    g_clear_error(&spawn_error);
    if (exit_status != 0) {
        return {
            .error = "curl 请求失败（退出码 " + to_string(exit_status)
                + "），请确认已安装 curl 且网络可用",
        };
    }
    return parse_ai_chat_response(response_body);
}

} // namespace

AiChatResult parse_ai_chat_response(string_view response_body) {
    try {
        const auto response = json::parse(response_body.begin(), response_body.end());
        if (response.contains("error")) {
            string message = "接口返回错误";
            if (response["error"].is_object()) {
                message = response["error"].value("message", message);
            }
            return {.error = std::move(message)};
        }
        return {
            .ok = true,
            .content = response.at("choices")
                .at(0)
                .at("message")
                .at("content")
                .get<string>(),
        };
    } catch (const exception& error) {
        return {.error = string("解析响应失败：") + error.what()};
    }
}

string strip_markdown_code_fence(string_view text) {
    string trimmed(text);
    const auto not_space = [](unsigned char value) {
        return !isspace(value);
    };
    trimmed.erase(trimmed.begin(), find_if(trimmed.begin(), trimmed.end(), not_space));
    trimmed.erase(
        find_if(trimmed.rbegin(), trimmed.rend(), not_space).base(), trimmed.end());

    if (trimmed.rfind("```", 0) != 0) {
        return trimmed;
    }
    const auto first_newline = trimmed.find('\n');
    if (first_newline == string::npos) {
        return trimmed;
    }
    trimmed = trimmed.substr(first_newline + 1);
    if (trimmed.size() >= 3
        && trimmed.compare(trimmed.size() - 3, 3, "```") == 0) {
        trimmed.resize(trimmed.size() - 3);
    }
    return trimmed;
}

optional<AiQuiz> parse_ai_quiz_response(string_view response_body) {
    try {
        const auto root = json::parse(strip_markdown_code_fence(response_body));
        const auto& values = root.at("questions");
        if (!values.is_array()) {
            return nullopt;
        }

        AiQuiz quiz;
        for (const auto& value : values) {
            try {
                AiQuizQuestion question {
                    .question = value.at("question").get<string>(),
                    .options = value.at("options").get<vector<string>>(),
                    .correct_indices =
                        value.at("correct_indices").get<vector<int>>(),
                    .explanation = value.value("explanation", ""),
                };
                question.correct_indices.erase(
                    remove_if(
                        question.correct_indices.begin(),
                        question.correct_indices.end(),
                        [&question](int index) {
                            return index < 0
                                || index >= static_cast<int>(question.options.size());
                        }),
                    question.correct_indices.end());
                sort(
                    question.correct_indices.begin(),
                    question.correct_indices.end());
                question.correct_indices.erase(
                    unique(
                        question.correct_indices.begin(),
                        question.correct_indices.end()),
                    question.correct_indices.end());
                if (question.question.empty() || question.options.empty()
                    || question.correct_indices.empty()) {
                    continue;
                }
                quiz.questions.push_back(std::move(question));
            } catch (const json::exception&) {
                continue;
            }
        }
        return quiz.questions.empty() ? nullopt : optional<AiQuiz>(std::move(quiz));
    } catch (const json::exception&) {
        return nullopt;
    }
}

int mastery_from_quiz_score(int correct_answers, int total_questions) {
    if (total_questions <= 0) {
        return 0;
    }
    const int bounded_correct = clamp(correct_answers, 0, total_questions);
    return bounded_correct * 5 / total_questions;
}

AiService::AiService()
    : m_transport(perform_ai_request) {}

AiService::AiService(AiTransport transport)
    : m_transport(std::move(transport)) {
    if (!m_transport) {
        throw invalid_argument("AI transport is required");
    }
}

AiChatResult AiService::chat(
    const AiCredentials& credentials,
    const string& prompt) const {
    if (!credentials.ark_api_key.empty()) {
        AiChatResult result = m_transport({
            .endpoint = kArkEndpoint,
            .model = kArkModel,
            .api_key = credentials.ark_api_key,
            .prompt = prompt,
        });
        if (result.ok || credentials.deepseek_api_key.empty()) {
            return result;
        }
        cerr << "豆包请求失败，回退到 DeepSeek：" << result.error << endl;
    }
    if (!credentials.deepseek_api_key.empty()) {
        return m_transport({
            .endpoint = kDeepseekEndpoint,
            .model = kDeepseekModel,
            .api_key = credentials.deepseek_api_key,
            .prompt = prompt,
        });
    }
    return {.error = "未配置任何 AI 服务商的 API Key"};
}
