#include "quiz_dialog.h"

#include "content/source_locator.h"
#include "services/ai_service.h"
#include "ui/ai_prompt_style.h"
#include "ui/dialog_helpers.h"

#include <algorithm>
#include <atomic>
#include <memory>
#include <string>
#include <thread>
#include <utility>
#include <vector>

using namespace std;

QuizDialog::QuizDialog(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    ApiKeyStore& api_keys,
    shared_ptr<atomic_bool> ui_alive)
    : m_parent(parent),
      m_content_loader(content_loader),
      m_api_keys(api_keys),
      m_ui_alive(std::move(ui_alive)) {}

// 打开对话框，异步向 AI（优先火山方舟豆包，失败或未配置再退回 DeepSeek）
// 请求针对该知识点具体源码的选择题（JSON 格式，每题含题干、选项、正确
// 选项下标和解释），逐题展示；每题先选一个选项，点“提交答案”才判对错、
// 给解释，颜色区分对错。返回的 JSON 解析失败时退化为纯文本展示，不崩溃、
// 不隐藏结果。
void QuizDialog::show(
    const DialogTopic& topic,
    function<bool(int)> on_mastery_changed) {
    const string ark_api_key = m_api_keys.ark_key();
    const string deepseek_api_key = m_api_keys.deepseek_key();
    if (ark_api_key.empty() && deepseek_api_key.empty()) {
        auto notice = Gtk::make_managed<Gtk::MessageDialog>(
            m_parent,
            "自测功能需要先在侧边栏底部“设置”里配置至少一个 AI "
            "服务商 Key",
            false,
            Gtk::MessageType::INFO,
            Gtk::ButtonsType::OK,
            true);
        notice->signal_response().connect([notice](int) { notice->hide(); });
        notice->show();
        return;
    }

    const string function_id = topic.function_id;
    const string topic_title = topic.title;
    string prompt =
        "请为 C++ 知识点「" + topic_title + "」生成一次可量化的掌握度自测。"
        "只能考察下面的知识点说明和参考实现能够支持的内容，不考范围外的"
        "冷门标准条款、编译器细节或文字陷阱。出题前先在内部列出独立考察"
        "点，确保核心语义、源码中的关键行为以及常见误用或边界情况都至少"
        "被一道题覆盖，但不要输出这份内部列表。题目数量由独立考察点的实际"
        "数量决定，少于 5 道或多于 5 道都可以，覆盖完整后立即停止；不要把"
        "同一事实换一种说法重复出题。优先使用短小、完整、可以实际分析的"
        "C++ 代码场景：例如判断输出或编译结果、跟踪对象和资源生命周期、"
        "识别所有权或异常安全问题、选择正确修改方案。能用代码场景考察的"
        "内容就不要改成纯定义背诵或措辞辩论；只有确实无法通过短代码表达"
        "时，才使用少量必要的概念题。只在知识点本身确有相关内容时考察边界"
        "与易错点；代码场景不得依赖未定义行为、特定编译器偶然表现或题目中"
        "没有说明的平台差异。"
        "不要用超出当前知识点范围的内容人为提高难度。每道题必须有能够由"
        "源码或明确 C++ 规则支持的答案，干扰项要合理但不能含糊。每题选项"
        "数量按题目需要决定；大多数题只有一个正确答案，确实有多个正确项"
        "时才做成多选题，并在 correct_indices 中列出全部正确选项。解释要"
        "简短说明正确依据及主要干扰项错在哪里。代码场景题把共享代码放进"
        "code 字段，不加 Markdown 代码围栏；不需要代码的题将 code 省略或"
        "设为空字符串。只用 JSON 格式返回，形如 "
        "{\"questions\":[{\"question\":"
        "\"...\",\"code\":\"...\",\"options\":[\"...\",\"...\"],"
        "\"correct_indices\":[0],"
        "\"explanation\":\"...\"}]}，correct_indices 是从 0 开始的正确"
        "选项下标数组，单选题这个数组只有一个元素。解释文字的" +
        string(kChineseTutorialStyleHint) +
        " 不要输出 JSON 之外的任何文字。\n\n知识点说明：" + topic.description;
    const auto body = load_member_source_text(
        m_content_loader, topic.source_path, topic.member_name);
    if (body && !body->empty()) {
        prompt += "\n\n参考实现：\n" + *body;
    }

    auto dialog = new Gtk::Dialog();
    dialog->set_title("知识点自测：" + topic_title);
    dialog->set_default_size(680, 560);

    auto* content = dialog->get_content_area();
    auto scrolled = Gtk::make_managed<Gtk::ScrolledWindow>();
    scrolled->set_hexpand(true);
    scrolled->set_vexpand(true);
    auto quiz_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 16);
    quiz_box->set_margin_top(8);
    quiz_box->set_margin_bottom(8);
    quiz_box->set_margin_start(8);
    quiz_box->set_margin_end(8);
    auto loading_label = Gtk::make_managed<Gtk::Label>("正在生成自测题，请稍候…");
    loading_label->add_css_class("dim-label");
    loading_label->add_css_class("ai-dialog-option");
    quiz_box->append(*loading_label);
    scrolled->set_child(*quiz_box);
    content->append(*scrolled);

    auto dialog_alive = make_shared<atomic_bool>(true);
    dialog->signal_hide().connect([dialog_alive]() { dialog_alive->store(false); });
    lock_for_modal_dialog(m_parent, *dialog);

    auto alive = m_ui_alive;
    thread([alive, dialog_alive, quiz_box, ark_api_key, deepseek_api_key, prompt,
            dialog, function_id, on_mastery_changed]() {
        const AiChatResult result = AiService().chat(
            {.ark_api_key = ark_api_key,
             .deepseek_api_key = deepseek_api_key},
            prompt);
        Glib::signal_idle().connect_once(
            [alive, dialog_alive, quiz_box, result, dialog, function_id,
             on_mastery_changed]() {
                if (!alive->load() || !dialog_alive->load()) {
                    return;
                }
                // 网络请求期间用户可能点过主窗口；结果到达时（不管题目
                // 是否解析成功）重新前置一次，不指望等待开始时的那次
                // present() 全程保持有效。
                dialog->present();
                while (auto* child = quiz_box->get_first_child()) {
                    quiz_box->remove(*child);
                }
                if (!result.ok) {
                    auto error_label = Gtk::make_managed<Gtk::Label>(
                        "请求失败：" + result.error);
                    error_label->set_halign(Gtk::Align::START);
                    error_label->set_wrap(true);
                    error_label->add_css_class("ai-dialog-option");
                    quiz_box->append(*error_label);
                    return;
                }

                const auto quiz = parse_ai_quiz_response(result.content);
                const bool parsed_ok = quiz.has_value();
                if (quiz) {
                    const int total_questions =
                        static_cast<int>(quiz->questions.size());
                    auto answered_questions = make_shared<int>(0);
                    auto correct_answers = make_shared<int>(0);
                    auto score_label = Gtk::make_managed<Gtk::Label>(
                        "完成全部 " + to_string(total_questions)
                        + " 道题后，将按本次成绩自动更新熟练度");
                    score_label->set_halign(Gtk::Align::START);
                    score_label->set_wrap(true);
                    score_label->set_xalign(0);
                    score_label->add_css_class("ai-dialog-feedback");
                    quiz_box->append(*score_label);

                    for (const auto& item : quiz->questions) {
                        const string question = item.question;
                        const string code = item.code;
                        const vector<string> options = item.options;
                        const vector<int> correct_indices = item.correct_indices;
                        const string explanation = item.explanation;
                        const bool is_multi_select = correct_indices.size() > 1;

                        auto item_box = Gtk::make_managed<Gtk::Box>(
                            Gtk::Orientation::VERTICAL, 8);

                        auto question_label = Gtk::make_managed<Gtk::Label>(
                            question
                            + (is_multi_select ? "（多选）" : ""));
                        question_label->set_halign(Gtk::Align::START);
                        question_label->set_wrap(true);
                        question_label->set_xalign(0);
                        question_label->add_css_class("ai-dialog-question");
                        item_box->append(*question_label);

                        if (!code.empty()) {
                            auto code_scrolled =
                                Gtk::make_managed<Gtk::ScrolledWindow>();
                            code_scrolled->set_policy(
                                Gtk::PolicyType::AUTOMATIC,
                                Gtk::PolicyType::NEVER);
                            const int line_count = static_cast<int>(
                                count(code.begin(), code.end(), '\n') + 1);
                            code_scrolled->set_min_content_height(
                                clamp(line_count * 28 + 20, 76, 272));
                            code_scrolled->add_css_class("ai-quiz-code-frame");

                            auto code_view =
                                Gtk::make_managed<Gtk::TextView>();
                            code_view->set_editable(false);
                            code_view->set_cursor_visible(false);
                            code_view->set_monospace(true);
                            code_view->set_wrap_mode(Gtk::WrapMode::NONE);
                            code_view->get_buffer()->set_text(code);
                            code_view->add_css_class("ai-quiz-code");
                            code_scrolled->set_child(*code_view);
                            item_box->append(*code_scrolled);
                        }

                        // 单选题的选项分到同一个 group（互斥，radio 行为）；
                        // 多选题的选项各自独立、可以同时勾选多个。
                        auto option_buttons =
                            make_shared<vector<Gtk::CheckButton*>>();
                        Gtk::CheckButton* first_option = nullptr;
                        for (const auto& option_text : options) {
                            auto option = Gtk::make_managed<Gtk::CheckButton>(
                                option_text);
                            option->add_css_class("ai-dialog-option");
                            if (!is_multi_select) {
                                if (first_option) {
                                    option->set_group(*first_option);
                                } else {
                                    first_option = option;
                                }
                            }
                            option_buttons->push_back(option);
                            item_box->append(*option);
                        }

                        auto feedback_label = Gtk::make_managed<Gtk::Label>();
                        feedback_label->set_halign(Gtk::Align::START);
                        feedback_label->set_wrap(true);
                        feedback_label->set_xalign(0);
                        feedback_label->add_css_class("ai-dialog-feedback");
                        feedback_label->set_visible(false);

                        auto explanation_label =
                            Gtk::make_managed<Gtk::Label>(explanation);
                        explanation_label->set_halign(Gtk::Align::START);
                        explanation_label->set_wrap(true);
                        explanation_label->set_xalign(0);
                        explanation_label->add_css_class("ai-dialog-explanation");
                        explanation_label->set_visible(false);

                        auto submit_button =
                            Gtk::make_managed<Gtk::Button>("提交答案");
                        submit_button->add_css_class("btn-sm");
                        submit_button->add_css_class("btn-ai-accent");
                        submit_button->set_halign(Gtk::Align::START);
                        submit_button->signal_clicked().connect(
                            [option_buttons,
                             correct_indices,
                             options,
                             feedback_label,
                             explanation_label,
                             submit_button,
                             answered_questions,
                             correct_answers,
                             total_questions,
                             score_label,
                             function_id,
                             on_mastery_changed]() {
                                vector<int> selected_indices;
                                for (size_t index = 0;
                                     index < option_buttons->size();
                                     ++index) {
                                    if ((*option_buttons)[index]->get_active()) {
                                        selected_indices.push_back(
                                            static_cast<int>(index));
                                    }
                                }
                                if (selected_indices.empty()) {
                                    feedback_label->set_text("请先选至少一个选项");
                                    feedback_label->remove_css_class("correct");
                                    feedback_label->remove_css_class("incorrect");
                                    feedback_label->set_visible(true);
                                    return;
                                }
                                // 多选题要求选中集合与正确答案集合完全一致
                                // 才算对，不给部分分。
                                auto sorted_selected = selected_indices;
                                auto sorted_correct = correct_indices;
                                sort(sorted_selected.begin(), sorted_selected.end());
                                sort(sorted_correct.begin(), sorted_correct.end());
                                const bool is_correct =
                                    sorted_selected == sorted_correct;
                                if (is_correct) {
                                    ++*correct_answers;
                                    feedback_label->set_text("✓ 回答正确");
                                } else {
                                    string correct_text;
                                    for (int index : sorted_correct) {
                                        if (!correct_text.empty()) {
                                            correct_text += "、";
                                        }
                                        correct_text +=
                                            options[static_cast<size_t>(index)];
                                    }
                                    feedback_label->set_text(
                                        "✗ 回答错误，正确答案是：" + correct_text);
                                }
                                feedback_label->remove_css_class("correct");
                                feedback_label->remove_css_class("incorrect");
                                feedback_label->add_css_class(
                                    is_correct ? "correct" : "incorrect");
                                feedback_label->set_visible(true);
                                explanation_label->set_visible(true);
                                for (auto* option : *option_buttons) {
                                    option->set_sensitive(false);
                                }
                                submit_button->set_sensitive(false);

                                ++*answered_questions;
                                if (*answered_questions == total_questions) {
                                    const int mastery = mastery_from_quiz_score(
                                        *correct_answers, total_questions);
                                    const bool saved =
                                        on_mastery_changed(mastery);
                                    score_label->set_text(
                                        "本次成绩：" + to_string(*correct_answers)
                                        + "/" + to_string(total_questions)
                                        + "，自动评定为 " + to_string(mastery)
                                        + " 星。"
                                        + (saved
                                               ? "评分已保存到学习进度。"
                                               : "评分暂时无法保存。"));
                                    if (mastery >= 5) {
                                        score_label->add_css_class("correct");
                                    }
                                    score_label->set_tooltip_text(
                                        "知识点 " + function_id
                                        + "：按正确率 × 5 向下取整；只有全对才是 5 星");
                                }
                            });
                        item_box->append(*submit_button);
                        item_box->append(*feedback_label);
                        item_box->append(*explanation_label);

                        quiz_box->append(*item_box);
                        quiz_box->append(*Gtk::make_managed<Gtk::Separator>());
                    }
                }

                if (!parsed_ok) {
                    // AI 没按要求的 JSON 格式返回时，原样展示文本，
                    // 至少不丢内容。
                    auto fallback_label =
                        Gtk::make_managed<Gtk::Label>(result.content);
                    fallback_label->set_halign(Gtk::Align::START);
                    fallback_label->set_wrap(true);
                    fallback_label->add_css_class("ai-dialog-option");
                    quiz_box->append(*fallback_label);
                }
            });
    }).detach();
}
