#include "code_chapter_page.h"

#include "ui/icon_utils.h"

#include <algorithm>
#include <iostream>
#include <vector>

using namespace std;

namespace {

const ChapterGroup* find_group(const ChapterMeta& chapter, const string& name) {
    const auto found = find_if(
        chapter.groups.begin(),
        chapter.groups.end(),
        [&name](const ChapterGroup& group) { return group.name == name; });
    return found == chapter.groups.end() ? nullptr : &*found;
}

DialogTopic make_dialog_topic(const auto& topic) {
    return {
        .function_id = topic.experiment.function_id,
        .title = topic.experiment.title,
        .description = topic.experiment.description,
        .source_path = topic.experiment.source_path,
        .member_name = topic.experiment.member_name,
    };
}

} // namespace

CodeChapterPage::CodeChapterPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const FunctionRegistry& function_registry,
    LearningStore* learning_store,
    LearningDialogs& dialogs,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested,
    function<void()> on_overview_requested,
    function<void()> on_progress_changed)
    : m_chapter(chapter),
      m_builder(builder),
      m_function_registry(function_registry),
      m_learning_store(learning_store),
      m_dialogs(dialogs),
      m_on_experiment_requested(std::move(on_experiment_requested)),
      m_on_progress_changed(std::move(on_progress_changed)) {
    m_header_title_label =
        builder->get_widget<Gtk::Label>("chapter_title_label");
    m_header_description_label =
        builder->get_widget<Gtk::Label>("chapter_description_label");
    m_header_icon = builder->get_widget<Gtk::Image>("chapter_icon");
    m_topics_list = builder->get_widget<Gtk::ListBox>("topics_list");
    m_knowledge_description_label =
        builder->get_widget<Gtk::Label>("knowledge_description_label");
    auto overview_button =
        builder->get_widget<Gtk::Button>("chapter_overview_button");

    if (m_header_title_label) {
        m_header_title_label->set_text(chapter.title);
    }
    if (m_header_description_label) {
        m_header_description_label->set_text(chapter.description);
    }
    if (m_header_icon) {
        configure_icon_image(*m_header_icon, chapter.icon, 36);
    }
    if (overview_button) {
        overview_button->signal_clicked().connect(
            std::move(on_overview_requested));
    }
    if (m_topics_list) {
        populate_topic_list();
    }
}

CodeChapterPage::~CodeChapterPage() {
    m_alive->store(false);
}

void CodeChapterPage::populate_topic_list() {
    if (m_chapter.subchapters.empty()) {
        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->set_selectable(false);
        row->set_activatable(false);
        auto label = Gtk::make_managed<Gtk::Label>("知识点框架待补充");
        label->set_halign(Gtk::Align::START);
        label->add_css_class("dim-label");
        label->set_margin(12);
        row->set_child(*label);
        m_topics_list->append(*row);
        if (m_knowledge_description_label) {
            m_knowledge_description_label->set_text(m_chapter.description);
        }
        return;
    }

    auto selection_by_row =
        make_shared<std::map<Gtk::ListBoxRow*, TopicSelection>>();
    auto activate_topic = make_shared<function<void(Gtk::ListBoxRow*)>>(
        [this, selection_by_row](Gtk::ListBoxRow* row) {
            const auto found = selection_by_row->find(row);
            if (found == selection_by_row->end()) {
                return;
            }
            for (const auto& entry : *selection_by_row) {
                entry.first->remove_css_class("topic-active");
            }
            row->add_css_class("topic-active");
            if (m_knowledge_description_label) {
                m_knowledge_description_label->set_text(
                    found->second.experiment.description);
            }
            if (m_header_title_label) {
                m_header_title_label->set_text(found->second.experiment.title);
            }
            if (m_header_description_label) {
                m_header_description_label->set_text(
                    found->second.experiment.description);
            }
            if (m_header_icon) {
                configure_icon_image(*m_header_icon, found->second.icon, 36);
            }
        });

    string current_group;
    for (const auto& subchapter : m_chapter.subchapters) {
        if (!subchapter.group.empty() && subchapter.group != current_group) {
            current_group = subchapter.group;
            if (const auto* group = find_group(m_chapter, current_group)) {
                auto header = Gtk::make_managed<Gtk::ListBoxRow>();
                header->set_selectable(false);
                header->set_activatable(false);
                header->add_css_class("topic-group");

                auto header_box = Gtk::make_managed<Gtk::Box>(
                    Gtk::Orientation::HORIZONTAL, 10);
                header_box->set_margin_top(12);
                header_box->set_margin_bottom(4);
                header_box->append(*make_icon_image(group->icon, 18));

                auto text_box = Gtk::make_managed<Gtk::Box>(
                    Gtk::Orientation::VERTICAL, 2);
                text_box->set_hexpand(true);
                auto title = Gtk::make_managed<Gtk::Label>(group->title);
                title->set_halign(Gtk::Align::START);
                title->add_css_class("heading");
                text_box->append(*title);
                auto description =
                    Gtk::make_managed<Gtk::Label>(group->description);
                description->set_halign(Gtk::Align::START);
                description->set_xalign(0);
                description->set_wrap(true);
                description->add_css_class("dim-label");
                text_box->append(*description);
                header_box->append(*text_box);
                header->set_child(*header_box);
                m_topics_list->append(*header);
            }
        }

        auto row = Gtk::make_managed<Gtk::ListBoxRow>();
        row->set_selectable(false);
        row->set_activatable(false);
        row->add_css_class("topic-row");
        (*selection_by_row)[row] = {
            .experiment =
                {.function_id = subchapter.function_id,
                 .title = subchapter.title,
                 .description = subchapter.description,
                 .source_path = subchapter.source,
                 .member_name = subchapter.name},
            .icon = subchapter.icon,
        };
        const TopicSelection topic = (*selection_by_row)[row];

        auto row_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 12);
        row_box->append(*make_icon_image(subchapter.icon, 20));
        auto text_box = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::VERTICAL, 4);
        text_box->set_hexpand(true);
        auto title_row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 8);
        auto point_title = Gtk::make_managed<Gtk::Label>(subchapter.title);
        point_title->set_halign(Gtk::Align::START);
        point_title->add_css_class("heading");
        title_row->append(*point_title);

        static const vector<string> importance_levels = {
            "未评", "简单", "一般", "正常", "复杂", "极难"};
        const int importance = clamp(subchapter.importance, 0, 5);
        if (importance > 0) {
            const string level_text =
                importance_levels[static_cast<size_t>(importance)];
            const string level_class =
                "importance-level-" + to_string(importance);
            auto group = Gtk::make_managed<Gtk::Box>(
                Gtk::Orientation::HORIZONTAL, 4);
            group->set_valign(Gtk::Align::CENTER);
            group->set_tooltip_text(
                "内容难度：" + level_text + "（由内容作者标注，只读）");
            auto badge = Gtk::make_managed<Gtk::Label>(level_text);
            badge->add_css_class("badge");
            badge->add_css_class("badge-importance");
            badge->add_css_class(level_class);
            group->append(*badge);
            auto stars = Gtk::make_managed<Gtk::Box>(
                Gtk::Orientation::HORIZONTAL, 6);
            stars->add_css_class("importance-stars");
            stars->add_css_class(level_class);
            for (int star_index = 1; star_index <= 5; ++star_index) {
                auto icon = Gtk::make_managed<Gtk::Image>();
                icon->set_from_icon_name(
                    star_index <= importance
                        ? "starred-symbolic"
                        : "non-starred-symbolic");
                icon->set_pixel_size(14);
                stars->append(*icon);
            }
            group->append(*stars);
            title_row->append(*group);
        }
        text_box->append(*title_row);

        auto point_description =
            Gtk::make_managed<Gtk::Label>(subchapter.description);
        point_description->set_halign(Gtk::Align::START);
        point_description->set_xalign(0);
        point_description->set_wrap(true);
        point_description->add_css_class("dim-label");
        text_box->append(*point_description);
        row_box->append(*text_box);

        auto actions = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 6);
        actions->set_valign(Gtk::Align::CENTER);
        actions->add_css_class("topic-actions");

        auto run = Gtk::make_managed<Gtk::Button>("运行");
        run->add_css_class("suggested-action");
        run->add_css_class("btn-primary");
        run->add_css_class("btn-sm");
        run->add_css_class("topic-run");
        const bool can_run =
            m_function_registry.contains(topic.experiment.function_id);
        run->set_sensitive(can_run);
        run->set_tooltip_text(can_run
            ? "运行该知识点的实验代码"
            : "该知识点尚未实现可运行实验");
        if (can_run) {
            run->signal_clicked().connect(
                [this, row, activate_topic, topic]() {
                    (*activate_topic)(row);
                    if (m_on_experiment_requested) {
                        m_on_experiment_requested(topic.experiment, true);
                    }
                });
        }
        actions->append(*run);

        auto history_button = Gtk::make_managed<Gtk::Button>("运行历史");
        history_button->add_css_class("btn-sm");
        history_button->set_tooltip_text("查看该知识点的运行记录");
        history_button->signal_clicked().connect(
            [this, row, activate_topic, topic]() {
                (*activate_topic)(row);
                m_dialogs.show_history(make_dialog_topic(topic));
            });
        actions->append(*history_button);

        auto insight_button = Gtk::make_managed<Gtk::Button>("AI 讲解");
        insight_button->add_css_class("btn-sm");
        insight_button->set_tooltip_text(
            "现场请 AI 从整体和局部两个角度讲解这段源码，结果会缓存、"
            "源码没变时下次直接展示；需要先在侧边栏底部“设置”里配置"
            "至少一个 AI 服务商 Key");
        insight_button->signal_clicked().connect(
            [this, row, activate_topic, topic]() {
                (*activate_topic)(row);
                m_dialogs.show_ai_insight(make_dialog_topic(topic));
            });
        actions->append(*insight_button);

        int saved_mastery = 0;
        if (m_learning_store) {
            try {
                saved_mastery =
                    m_learning_store->load_mastery(topic.experiment.function_id);
            } catch (const exception& error) {
                cerr << "Failed to load progress for "
                     << topic.experiment.function_id
                     << ": " << error.what() << endl;
            }
        }
        auto mastery = make_shared<int>(clamp(saved_mastery, 0, 5));
        auto mastery_row = Gtk::make_managed<Gtk::Box>(
            Gtk::Orientation::HORIZONTAL, 4);
        mastery_row->add_css_class("star-row");
        mastery_row->add_css_class("star-row-mastery");
        mastery_row->set_tooltip_text(
            "熟练度由最近一次完成的 AI 自测成绩自动评定，不能手动修改");
        auto caption = Gtk::make_managed<Gtk::Label>("熟练度");
        caption->add_css_class("star-caption");
        mastery_row->append(*caption);

        auto mastery_stars = make_shared<vector<Gtk::Image*>>();
        for (int index = 0; index < 5; ++index) {
            auto star = Gtk::make_managed<Gtk::Image>();
            star->set_pixel_size(14);
            mastery_stars->push_back(star);
            mastery_row->append(*star);
        }
        auto mastery_label = Gtk::make_managed<Gtk::Label>();
        mastery_label->add_css_class("star-level-label");
        mastery_label->set_halign(Gtk::Align::START);
        mastery_row->append(*mastery_label);

        auto refresh_mastery = make_shared<function<void()>>();
        *refresh_mastery = [mastery, mastery_stars, mastery_label]() {
            const int level = clamp(*mastery, 0, 5);
            for (size_t index = 0; index < mastery_stars->size(); ++index) {
                (*mastery_stars)[index]->set_from_icon_name(
                    static_cast<int>(index) < level
                        ? "starred-symbolic"
                        : "non-starred-symbolic");
            }
            mastery_label->set_text(to_string(level) + " 星");
        };
        (*refresh_mastery)();

        auto page_alive = m_alive;
        auto update_mastery =
            [this,
             page_alive,
             function_id = topic.experiment.function_id,
             mastery,
             refresh_mastery](int score) {
                if (!page_alive->load()) {
                    return false;
                }
                *mastery = clamp(score, 0, 5);
                (*refresh_mastery)();
                if (!m_learning_store) {
                    return false;
                }
                try {
                    m_learning_store->save_mastery(function_id, *mastery);
                    if (m_on_progress_changed) {
                        m_on_progress_changed();
                    }
                    return true;
                } catch (const exception& error) {
                    cerr << "Failed to save quiz score for " << function_id
                         << ": " << error.what() << endl;
                    return false;
                }
            };

        auto quiz_button = Gtk::make_managed<Gtk::Button>("AI 自测");
        quiz_button->add_css_class("btn-sm");
        quiz_button->set_tooltip_text(
            "需要先在侧边栏底部“设置”里配置至少一个 AI 服务商 Key。题目"
            "依据当前知识点说明和真实源码生成；完成全部题目后由本地规则"
            "自动评分并更新熟练度");
        quiz_button->signal_clicked().connect(
            [this, row, activate_topic, topic, update_mastery]() {
                (*activate_topic)(row);
                m_dialogs.show_quiz(make_dialog_topic(topic), update_mastery);
            });
        actions->append(*quiz_button);
        actions->append(*mastery_row);
        row_box->append(*actions);
        row->set_child(*row_box);
        m_topics_list->append(*row);
    }
}
