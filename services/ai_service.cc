#include "ai_service.h"

#include <glib.h>
#include <glib/gstdio.h>
#include <nlohmann/json.hpp>

#include <algorithm>
#include <cerrno>
#include <cctype>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <utility>

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

struct TempFileResult {
    string path;
    string error;
};

TempFileResult write_secure_temp_file(
    const string& name_template,
    const string& content) {
    const char* cache_root = g_get_user_cache_dir();
    if (!cache_root || !*cache_root) {
        return {.error = "无法确定用户缓存目录"};
    }

    gchar* temp_dir = g_build_filename(cache_root, "Athena", "tmp", nullptr);
    if (g_mkdir_with_parents(temp_dir, 0700) != 0) {
        const string message = g_strerror(errno);
        g_free(temp_dir);
        return {.error = "无法创建 Athena 缓存目录：" + message};
    }

    gchar* path_raw =
        g_build_filename(temp_dir, name_template.c_str(), nullptr);
    g_free(temp_dir);
    GError* file_error = nullptr;
    const gint fd = g_mkstemp(path_raw);
    if (fd < 0) {
        const string message = g_strerror(errno);
        g_free(path_raw);
        return {.error = message};
    }
    const string path = path_raw;
    g_free(path_raw);

    if (!g_close(fd, &file_error)) {
        const string message = file_error
            ? file_error->message
            : "关闭临时文件失败";
        g_clear_error(&file_error);
        g_remove(path.c_str());
        return {.error = message};
    }
    g_clear_error(&file_error);

    ofstream stream(path, ios::binary);
    stream << content;
    stream.close();
    if (!stream) {
        g_remove(path.c_str());
        return {.error = "写入临时文件失败"};
    }
    return {.path = path};
}

AiChatResult perform_ai_request(const AiChatRequest& request) {
    const json request_body = {
        {"model", request.model},
        {"messages",
         json::array({{{"role", "user"}, {"content", request.prompt}}})},
        {"stream", false},
    };

    // g_mkstemp() 要求模板以六个 X 结尾。文件放在 Athena 自己的用户缓存
    // 目录中，不依赖启动进程传入的 TMPDIR；后者可能指向已经被系统清理的
    // 安装沙箱目录，使请求在发出前失败。
    const TempFileResult config_file = write_secure_temp_file(
        "athena-ai-chat-cfg-XXXXXX",
        "header = \"Authorization: Bearer " + request.api_key + "\"\n"
        "header = \"Content-Type: application/json\"\n");
    const TempFileResult body_file = write_secure_temp_file(
        "athena-ai-chat-json-XXXXXX", request_body.dump());

    struct TempFileGuard {
        vector<string> paths;
        ~TempFileGuard() {
            for (const auto& path : paths) {
                if (!path.empty()) {
                    g_remove(path.c_str());
                }
            }
        }
    } guard {{config_file.path, body_file.path}};

    if (config_file.path.empty() || body_file.path.empty()) {
        const string detail = !config_file.error.empty()
            ? config_file.error
            : body_file.error;
        return {
            .error = "无法创建临时请求文件：" + detail,
        };
    }

    const string command = "curl -sS --max-time 30 --connect-timeout 10 -K "
        + shell_quote(config_file.path) + " --data @"
        + shell_quote(body_file.path)
        + " " + shell_quote(request.endpoint);
    gchar* output_raw = nullptr;
    gint wait_status = 0;
    GError* spawn_error = nullptr;
    const gboolean spawned = g_spawn_command_line_sync(
        command.c_str(),
        &output_raw,
        nullptr,
        &wait_status,
        &spawn_error);
    const string response_body = output_raw ? output_raw : "";
    g_free(output_raw);

    if (!spawned) {
        const string message = spawn_error ? spawn_error->message : "未知错误";
        g_clear_error(&spawn_error);
        return {.error = "调用 curl 失败：" + message};
    }
    g_clear_error(&spawn_error);
    // g_spawn_command_line_sync() 的 status 是 waitpid 原始状态字（macOS 和
    // Linux 都是），不能直接当退出码比较；交给 GLib 解析退出码/信号终止。
    if (!g_spawn_check_wait_status(wait_status, &spawn_error)) {
        const string message = spawn_error ? spawn_error->message : "未知错误";
        g_clear_error(&spawn_error);
        return {
            .error = "curl 请求失败（" + message
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
        // 提示词要求外层包一层 {"questions": [...]}，但 AI 偶尔会省略这层包装、
        // 直接返回题目数组本身；两种形状都接受，避免因为差这一层包装就整份
        // 退化成原始文本展示。root.at("questions") 在 root 是数组时会抛
        // out_of_range（数组没有名为 "questions" 的键），被下面的 catch 接住，
        // 不会导致解析失败之外的任何后果。
        const auto& values = root.is_array() ? root : root.at("questions");
        if (!values.is_array()) {
            return nullopt;
        }

        AiQuiz quiz;
        for (const auto& value : values) {
            try {
                AiQuizQuestion question {
                    .question = value.at("question").get<string>(),
                    .code = value.value("code", ""),
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
    // 默认顺序改成 DeepSeek 优先、火山方舟豆包兜底——2026-08 体感豆包
    // 响应明显更慢，先换 DeepSeek 试一下速度；两边都是 OpenAI 兼容协议，
    // 只是 endpoint/model 不同，顺序调换不影响别处的调用方式。如果后续
    // 要改回来或者做成可配置项，只需要改这一处顺序。
    if (!credentials.deepseek_api_key.empty()) {
        AiChatResult result = m_transport({
            .endpoint = kDeepseekEndpoint,
            .model = kDeepseekModel,
            .api_key = credentials.deepseek_api_key,
            .prompt = prompt,
        });
        if (result.ok || credentials.ark_api_key.empty()) {
            return result;
        }
        cerr << "DeepSeek 请求失败，回退到豆包：" << result.error << endl;
    }
    if (!credentials.ark_api_key.empty()) {
        return m_transport({
            .endpoint = kArkEndpoint,
            .model = kArkModel,
            .api_key = credentials.ark_api_key,
            .prompt = prompt,
        });
    }
    return {.error = "未配置任何 AI 服务商的 API Key"};
}
