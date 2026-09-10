#include "type_semantics_lesson_page.h"

#include "render/cairo_text.h"
#include "ui/learning_unit_view.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

using namespace std;

namespace {

const SubChapter& topic_by_name(
    const ChapterMeta& chapter, const string& subchapter_name) {
    for (const auto& subchapter : chapter.subchapters) {
        if (subchapter.name == subchapter_name) {
            return subchapter;
        }
    }
    throw runtime_error(
        "TypeSemantics lesson requires topic " + subchapter_name);
}

string function_id_of(const ChapterMeta& chapter, const string& subchapter_name) {
    return topic_by_name(chapter, subchapter_name).function_id;
}

string repeat_star(int count) {
    string stars;
    for (int index = 0; index < count; ++index) {
        stars += "★";
    }
    return stars;
}

// 平均熟练度落在哪一档：完全没碰过、学习中、已全部掌握。三档语义与
// 知识图谱节点一致，直接复用它的配色。
const char* mastery_tier(double average_mastery) {
    if (average_mastery <= 0.0) {
        return "mastery-none";
    }
    if (average_mastery >= 5.0) {
        return "mastery-all";
    }
    return "mastery-some";
}

// 对象图配色取 Bootstrap 语义色，与 style.css 的 @athena_* 和手册一致，不自定义：
// 独立对象框 = success 绿，名字 / 别名标签 = primary 蓝，被改动的值 = danger 红。
constexpr ChartColor kObjStroke{0.094, 0.529, 0.329};   // #198754 success
constexpr ChartColor kObjFill{0.820, 0.906, 0.867};     // #d1e7dd
constexpr ChartColor kNameStroke{0.039, 0.345, 0.792};  // #0a58ca primary
constexpr ChartColor kNameFill{0.812, 0.886, 1.000};    // #cfe2ff
constexpr ChartColor kChanged{0.863, 0.208, 0.271};     // #dc3545 danger
constexpr ChartColor kInk{0.129, 0.145, 0.161};         // #212529
constexpr ChartColor kMuted{0.424, 0.459, 0.490};       // #6c757d

void rounded_box(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double x,
    double y,
    double width,
    double height,
    const ChartColor& border,
    const ChartColor& fill,
    bool dashed = false) {
    const double radius = 8.0;
    cr->begin_new_sub_path();
    cr->arc(x + width - radius, y + radius, radius, -M_PI / 2, 0);
    cr->arc(x + width - radius, y + height - radius, radius, 0, M_PI / 2);
    cr->arc(x + radius, y + height - radius, radius, M_PI / 2, M_PI);
    cr->arc(x + radius, y + radius, radius, M_PI, 3 * M_PI / 2);
    cr->close_path();
    cr->set_source_rgb(fill.r, fill.g, fill.b);
    cr->fill_preserve();
    cr->set_source_rgb(border.r, border.g, border.b);
    cr->set_line_width(1.6);
    if (dashed) {
        cr->set_dash(vector<double>{4.0, 3.0}, 0.0);
    } else {
        cr->unset_dash();
    }
    cr->stroke();
    cr->unset_dash();
}

} // namespace

TypeSemanticsLessonPage::TypeSemanticsLessonPage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    const map<string, int>& mastery_by_id,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested,
    function<void()> on_reference_requested)
    : m_chapter(chapter),
      m_on_experiment_requested(std::move(on_experiment_requested)) {
    auto* init_unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_learning_unit_host");
    auto* run_button =
        builder->get_widget<Gtk::Button>("type_semantics_run_button");
    auto* reference_button = builder->get_widget<Gtk::Button>(
        "type_semantics_reference_button");
    m_section_notebook = builder->get_widget<Gtk::Notebook>(
        "type_semantics_section_notebook");
    auto* deduction_unit_host = builder->get_widget<Gtk::Box>(
        "type_semantics_deduction_unit_host");
    auto* deduction_variant_host = builder->get_widget<Gtk::Box>(
        "type_semantics_deduction_variant_host");
    m_deduction_graph = builder->get_widget<Gtk::DrawingArea>(
        "type_semantics_deduction_graph");
    m_anim_status =
        builder->get_widget<Gtk::Label>("ts_deduction_anim_status");
    m_anim_note = builder->get_widget<Gtk::Label>("ts_deduction_anim_note");
    m_anim_playpause =
        builder->get_widget<Gtk::Button>("ts_deduction_anim_playpause");
    auto* anim_prev =
        builder->get_widget<Gtk::Button>("ts_deduction_anim_prev");
    auto* anim_next =
        builder->get_widget<Gtk::Button>("ts_deduction_anim_next");
    auto* anim_reset =
        builder->get_widget<Gtk::Button>("ts_deduction_anim_reset");
    if (!init_unit_host || !run_button || !reference_button
        || !m_section_notebook || !deduction_unit_host
        || !deduction_variant_host || !m_deduction_graph || !m_anim_status
        || !m_anim_note || !m_anim_playpause || !anim_prev || !anim_next
        || !anim_reset) {
        throw runtime_error("Failed to load TypeSemantics lesson Blueprint");
    }

    // 教案内嵌的静态 SVG 图与手册共享同一批资产（resources/articles/cpp/images/），
    // 打包进 /app 前缀的 GResource；结构留在 Blueprint，这里只填图源。
    const vector<pair<const char*, const char*>> lesson_figures = {
        {"ts_map_figure", "/app/articles/cpp/images/type_semantics_map.svg"},
        {"ts_init_forms_figure", "/app/articles/cpp/images/init_forms.svg"},
        {"ts_auto_selection_figure",
         "/app/articles/cpp/images/auto_selection_flow.svg"},
        {"ts_lifetime_figure",
         "/app/articles/cpp/images/object_lifetime_timeline.svg"},
    };
    for (const auto& [figure_id, resource_path] : lesson_figures) {
        if (auto* figure = builder->get_widget<Gtk::Picture>(figure_id)) {
            figure->set_resource(resource_path);
        }
    }

    add_learning_unit(
        *init_unit_host,
        LearningUnit{
            .id = "narrowing_boundary",
            .heading = "",
            .claim = "花括号初始化会把可能丢失信息的窄化转换拦在编译期。",
            .question =
                "double source = 3.75; int value{source}; 这行代码会怎样？",
            .choices = {
                "通过编译，并把 3.75 截断为 3",
                "编译失败，因为列表初始化拒绝窄化",
            },
            .correct_choice = 1,
            .feedback = "小数部分可能丢失，因此列表初始化在编译期拒绝它。圆括号初始化才允许调用者明确接受截断。",
            .follow_up = "实验里再观察 int value(source) 为什么能运行，却需要由调用者承担截断。",
            .experiment_function_id =
                function_id_of(m_chapter, "initialization"),
        },
        "initialization");

    add_learning_unit(
        *deduction_unit_host,
        LearningUnit{
            .id = "const_view_sees_new_value",
            .heading = "",
            .claim = "const auto& view 是只读的访问路径，不是一份冻结的旧值快照。",
            .question =
                "接上例，现在通过 original 把值改成 120。view 随后读到多少？",
            .choices = {
                "120，因为 view 仍访问同一个对象",
                "99，因为只读会冻结数值",
                "无法读取，因为原对象变过",
            },
            .correct_choice = 0,
            .feedback = "view 读到 120。const 限制的是“通过 view 修改对象”，不是保存一张旧值快照。要保留旧值，用值副本；要观察当前值，用别名。",
            .follow_up = "回到实验源码，确认 view 这一行从头到尾没有复制 original。",
            .experiment_function_id =
                function_id_of(m_chapter, "auto_deduction"),
        },
        "auto_deduction");

    add_learning_unit(
        *deduction_variant_host,
        LearningUnit{
            .id = "const_ref_deduction_variant",
            .heading = "",
            .claim = "把 auto copy 换成 const auto& copy，语义完全不同。",
            .question =
                "const auto& copy = original; 之后写 copy = 20; 会怎样？",
            .choices = {
                "能编译，引用可以赋值",
                "编译失败，copy 是只读别名",
                "不确定",
            },
            .correct_choice = 1,
            .feedback = "const auto& 推出的是 const int&：copy 成了 original 的只读别名，既不能改它、也不再是独立对象。一次只改一个条件，才能看清 auto、auto&、const auto& 的边界。",
            .follow_up = "回到 auto 实验源码，确认 const 引用为什么不能出现在赋值号左边。",
            .experiment_function_id =
                function_id_of(m_chapter, "auto_deduction"),
        },
        "auto_deduction");

    m_deduction_graph->set_draw_func(
        [this](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_deduction_graph(cr, width, height);
        });
    anim_prev->signal_clicked().connect([this]() {
        set_anim_playing(false);
        set_anim_step(m_anim_step - 1);
    });
    anim_next->signal_clicked().connect([this]() {
        set_anim_playing(false);
        set_anim_step(m_anim_step + 1);
    });
    anim_reset->signal_clicked().connect([this]() {
        set_anim_playing(false);
        set_anim_step(0);
    });
    m_anim_playpause->signal_clicked().connect(
        [this]() { set_anim_playing(!m_anim_playing); });
    set_anim_step(0);

    run_button->signal_clicked().connect(
        [this]() { open_experiment("initialization"); });
    reference_button->signal_clicked().connect(std::move(on_reference_requested));

    const vector<pair<const char*, const char*>> experiment_buttons = {
        {"type_semantics_auto_button", "auto_deduction"},
        {"type_semantics_decltype_button", "decltype_deduction"},
        {"type_semantics_lifetime_button", "object_lifetime"},
        {"type_semantics_value_category_button", "value_category"},
        {"type_semantics_cast_button", "cast"},
        {"type_semantics_enum_button", "enum_class"},
    };
    for (const auto& [widget_id, topic_name] : experiment_buttons) {
        auto* button = builder->get_widget<Gtk::Button>(widget_id);
        if (!button) {
            throw runtime_error(
                string("Missing TypeSemantics lesson button: ") + widget_id);
        }
        button->signal_clicked().connect(
            [this, topic_name]() { open_experiment(topic_name); });
    }

    // 标签顺序必须与 type_semantics_lesson.blp 中 Notebook 页顺序一致。
    // 一个标签是一个学习小节，可能覆盖不止一个知识点。
    // 顺序与 type_semantics_lesson.blp 中 Notebook 的页顺序一致：概念主线
    // 讲完后，「初始化」作为结合真实源码的动手验证节放在最后。
    m_section_tabs = {
        {"教学大纲", {}},
        {"本章导览", {}},
        {"类型推导", {"auto_deduction", "decltype_deduction"}},
        {"对象生命周期", {"object_lifetime"}},
        {"值类别", {"value_category"}},
        {"类型转换", {"cast"}},
        {"enum class", {"enum_class"}},
        {"初始化", {"initialization"}},
    };
    render_overview(builder, content_loader);
    apply_tab_labels(mastery_by_id);
}

void TypeSemanticsLessonPage::render_overview(
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader) {
    auto* host = builder->get_widget<Gtk::Box>("type_semantics_overview_host");
    if (host == nullptr) {
        cerr << "TypeSemantics lesson: overview host missing from Blueprint"
             << endl;
        return;
    }
    if (m_chapter.overview_document.empty()) {
        cerr << "TypeSemantics lesson: chapter has no overview_document" << endl;
        return;
    }

    const string markdown =
        content_loader.load_document(m_chapter.overview_document);
    if (markdown.empty()) {
        cerr << "TypeSemantics lesson: failed to load "
             << m_chapter.overview_document << endl;
        return;
    }

    // 与手册一致：图片按大纲所在目录解析，于是 Markdown 里的
    // images/xxx.svg 落到 /app/articles/cpp/images/xxx.svg。
    constexpr string_view resources_prefix = "resources/";
    string relative = m_chapter.overview_document;
    if (relative.rfind(resources_prefix, 0) == 0) {
        relative = relative.substr(resources_prefix.size());
    }
    const auto slash = relative.find_last_of('/');
    const string resource_base =
        slash == string::npos ? "/app/" : "/app/" + relative.substr(0, slash + 1);

    try {
        m_overview_view = make_unique<DocumentView>(resource_base);
        auto& view = m_overview_view->widget();
        // 大纲占用 Notebook 的完整页面，由 DocumentView 自己负责滚动；
        // 不再嵌入折叠框，也不设置固定高度。
        view.set_vexpand(true);
        host->append(view);
        m_overview_view->set_markdown(markdown);
    } catch (const exception& error) {
        cerr << "TypeSemantics lesson: failed to render overview: "
             << error.what() << endl;
        m_overview_view.reset();
    }
}

LearningUnitView& TypeSemanticsLessonPage::add_learning_unit(
    Gtk::Box& host, LearningUnit data, const string& verify_subchapter) {
    m_unit_data.push_back(make_unique<LearningUnit>(std::move(data)));
    auto view = make_unique<LearningUnitView>(
        *m_unit_data.back(),
        [this, verify_subchapter](const string&) {
            open_experiment(verify_subchapter);
        });
    host.append(view->widget());
    m_unit_views.push_back(std::move(view));
    return *m_unit_views.back();
}

namespace {

// 名字标签 → 对象框的一条连线（虚线表示“只是另一个名字”），末端画箭头。
void name_link(
    const Cairo::RefPtr<Cairo::Context>& cr,
    double fx,
    double fy,
    double tx,
    double ty,
    const ChartColor& color) {
    cr->set_source_rgb(color.r, color.g, color.b);
    cr->set_line_width(1.6);
    cr->set_dash(vector<double>{4.0, 3.0}, 0.0);
    cr->move_to(fx, fy);
    cr->line_to(tx, ty);
    cr->stroke();
    cr->unset_dash();

    const double angle = atan2(ty - fy, tx - fx);
    cr->move_to(tx, ty);
    cr->line_to(
        tx - 7.0 * cos(angle - 0.4), ty - 7.0 * sin(angle - 0.4));
    cr->line_to(
        tx - 7.0 * cos(angle + 0.4), ty - 7.0 * sin(angle + 0.4));
    cr->close_path();
    cr->fill();
}

} // namespace

void TypeSemanticsLessonPage::draw_deduction_graph(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) const {
    const int step = m_anim_step;
    const double w = static_cast<double>(width);

    const double box_w = 150.0;
    const double box_h = 62.0;
    const double obj_y = 96.0;
    // 固定宽度的一簇：original 右缘到 copy 左缘留 210px 放 alias / view 标签，
    // 整簇在画布里居中，避免宽屏下把 copy 推到很远、虚线拉得过长。
    const double gap_between = 210.0;
    const double cluster_w = box_w * 2.0 + gap_between;
    const double orig_x = max(28.0, (w - cluster_w) / 2.0);
    const double copy_x = orig_x + box_w + gap_between;
    const double tag_cx = orig_x + box_w + gap_between / 2.0;

    // original：独立对象。step 5 起值变 99，改动的那一步描边高亮。
    const bool orig_changed = step == 5;
    const char* orig_value = step >= 5 ? "99" : "42";
    rounded_box(
        cr, orig_x, obj_y, box_w, box_h, orig_changed ? kChanged : kObjStroke,
        kObjFill);
    draw_cairo_text(
        cr, "original", orig_x + box_w / 2.0, obj_y - 12.0, 12.0, kMuted, false,
        0.5);
    draw_cairo_text(
        cr, orig_value, orig_x + box_w / 2.0, obj_y + box_h / 2.0, 18.0,
        orig_changed ? kChanged : kInk, true, 0.5);

    // copy：step 1 起出现，step 4 起值变 7。
    if (step >= 1) {
        const bool copy_changed = step == 1 || step == 4;
        const char* copy_value = step >= 4 ? "7" : "42";
        rounded_box(
            cr, copy_x, obj_y, box_w, box_h,
            copy_changed ? kChanged : kObjStroke, kObjFill);
        draw_cairo_text(
            cr, "copy", copy_x + box_w / 2.0, obj_y - 12.0, 12.0, kMuted, false,
            0.5);
        draw_cairo_text(
            cr, copy_value, copy_x + box_w / 2.0, obj_y + box_h / 2.0, 18.0,
            step == 4 ? kChanged : kInk, true, 0.5);
    }

    // alias：step 2 起出现的名字标签，虚线连到 original 顶部；step 5 高亮。
    if (step >= 2) {
        const double tag_w = 116.0;
        const double tag_h = 30.0;
        const double tag_y = 20.0;
        rounded_box(
            cr, tag_cx - tag_w / 2.0, tag_y, tag_w, tag_h,
            step == 5 ? kChanged : kNameStroke, kNameFill);
        draw_cairo_text(
            cr, "alias", tag_cx, tag_y + tag_h / 2.0, 13.0, kInk, true, 0.5);
        name_link(
            cr, tag_cx, tag_y + tag_h, orig_x + box_w * 0.62, obj_y,
            step == 5 ? kChanged : kNameStroke);
    }

    // view：step 3 起出现，只读访问路径，虚线连到 original 底部；step 6 高亮。
    if (step >= 3) {
        const double tag_w = 150.0;
        const double tag_h = 30.0;
        const double tag_y = obj_y + box_h + 34.0;
        rounded_box(
            cr, tag_cx - tag_w / 2.0, tag_y, tag_w, tag_h,
            step == 6 ? kChanged : kNameStroke, kNameFill);
        draw_cairo_text(
            cr, "view（只读）", tag_cx, tag_y + tag_h / 2.0, 13.0, kInk, true,
            0.5);
        name_link(
            cr, tag_cx, tag_y, orig_x + box_w * 0.62, obj_y + box_h,
            step == 6 ? kChanged : kNameStroke);
        if (step == 6) {
            draw_cairo_text(
                cr, "✗ view = 20 被规则拒绝", tag_cx, tag_y + tag_h + 16.0,
                12.5, kChanged, true, 0.5);
        }
    }

    draw_cairo_text(
        cr,
        "绿框 = 各自独立的整数对象     蓝标签 = 指向同一个对象的名字",
        w / 2.0, static_cast<double>(height) - 12.0, 12.0, kMuted, false, 0.5);
}

TypeSemanticsLessonPage::~TypeSemanticsLessonPage() { m_anim_timer.disconnect(); }

void TypeSemanticsLessonPage::set_anim_step(int step) {
    m_anim_step = clamp(step, 0, kDeductionAnimSteps);

    static const array<const char*, kDeductionAnimSteps + 1> notes = {
        "起点：创建 original，值是 42。点“下一步”或“播放”逐步观察。",
        "初始化 copy：用 original 当前的值，得到第二个独立的整数（同为 42）。",
        "绑定 alias：给 original 增加一个名字，没有新的整数。",
        "绑定 view：original 的只读访问路径，不能通过它赋值。",
        "copy = 7：改的是独立副本，original 仍然是 42。",
        "alias = 99：通过别名改了 original；view 现在读到 99；copy 仍是 7。",
        "试图 view = 20：被规则拒绝（只读路径），数值不变。这是规则说明，不是"
        "编译器诊断。",
    };
    if (m_anim_note != nullptr) {
        m_anim_note->set_text(notes[static_cast<size_t>(m_anim_step)]);
    }
    if (m_anim_status != nullptr) {
        m_anim_status->set_text(
            "步骤 " + to_string(m_anim_step) + " / "
            + to_string(kDeductionAnimSteps));
    }
    if (m_deduction_graph != nullptr) {
        m_deduction_graph->queue_draw();
    }
}

void TypeSemanticsLessonPage::set_anim_playing(bool playing) {
    if (playing == m_anim_playing) {
        return;
    }
    m_anim_playing = playing;
    if (m_anim_playpause != nullptr) {
        m_anim_playpause->set_label(playing ? "暂停" : "播放");
    }
    if (playing) {
        if (m_anim_step >= kDeductionAnimSteps) {
            set_anim_step(0);
        }
        m_anim_timer = Glib::signal_timeout().connect(
            sigc::mem_fun(*this, &TypeSemanticsLessonPage::on_anim_tick), 950);
    } else {
        m_anim_timer.disconnect();
    }
}

bool TypeSemanticsLessonPage::on_anim_tick() {
    if (m_anim_step >= kDeductionAnimSteps) {
        set_anim_playing(false);
        return false;
    }
    set_anim_step(m_anim_step + 1);
    if (m_anim_step >= kDeductionAnimSteps) {
        set_anim_playing(false);
        return false;
    }
    return true;
}

void TypeSemanticsLessonPage::refresh_progress(
    const map<string, int>& mastery_by_id) {
    apply_tab_labels(mastery_by_id);
}

void TypeSemanticsLessonPage::apply_tab_labels(
    const map<string, int>& mastery_by_id) {
    if (m_section_notebook == nullptr) {
        return;
    }
    const int page_count = m_section_notebook->get_n_pages();
    if (page_count != static_cast<int>(m_section_tabs.size())) {
        cerr << "TypeSemantics lesson: Notebook has " << page_count
             << " pages but " << m_section_tabs.size()
             << " section descriptors; tab styling skipped" << endl;
        return;
    }
    for (int index = 0; index < page_count; ++index) {
        auto* page = m_section_notebook->get_nth_page(index);
        if (page == nullptr) {
            continue;
        }
        m_section_notebook->set_tab_label(
            *page,
            *build_tab_label(
                m_section_tabs[static_cast<size_t>(index)], mastery_by_id));
    }
}

Gtk::Widget* TypeSemanticsLessonPage::build_tab_label(
    const SectionTab& section, const map<string, int>& mastery_by_id) const {
    int difficulty = 0;
    // 一个标签可能覆盖多个知识点，取其中最高的掌握目标：只要有一个要求精通，
    // 整个小节就不能按"了解一下"对待。
    MasteryGoal goal = MasteryGoal::Unrated;
    const auto goal_rank = [](MasteryGoal value) {
        switch (value) {
        case MasteryGoal::Master:
            return 3;
        case MasteryGoal::Required:
            return 2;
        case MasteryGoal::Familiar:
            return 1;
        case MasteryGoal::Unrated:
            break;
        }
        return 0;
    };
    double mastery_sum = 0.0;
    int mastery_count = 0;
    for (const auto& subchapter_name : section.subchapter_names) {
        const auto& subchapter = topic_by_name(m_chapter, subchapter_name);
        difficulty = max(difficulty, subchapter.difficulty);
        if (goal_rank(subchapter.mastery_goal) > goal_rank(goal)) {
            goal = subchapter.mastery_goal;
        }
        const auto found = mastery_by_id.find(subchapter.function_id);
        mastery_sum += found == mastery_by_id.end() ? 0.0 : found->second;
        ++mastery_count;
    }
    const double average_mastery =
        mastery_count == 0 ? 0.0 : mastery_sum / mastery_count;

    auto* row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    row->add_css_class("lesson-tab");

    auto* title = Gtk::make_managed<Gtk::Label>(section.title);
    title->add_css_class("lesson-tab-title");
    row->append(*title);

    // 合成小节（如“教学大纲”“本章导览”）没有知识点，不显示难度星和掌握度圆点。
    if (section.subchapter_names.empty()) {
        return row;
    }

    if (difficulty > 0) {
        auto* stars = Gtk::make_managed<Gtk::Label>(repeat_star(difficulty));
        stars->add_css_class("lesson-tab-stars");
        stars->add_css_class("difficulty-level-" + to_string(difficulty));
        stars->set_tooltip_text(
            "知识点难度 " + to_string(difficulty)
            + " / 5（1-3 初中级，4-5 高级）");
        row->append(*stars);
    }

    if (goal != MasteryGoal::Unrated) {
        static const map<MasteryGoal, pair<const char*, const char*>> goal_marks =
            {
                {MasteryGoal::Master, {"精通", "mastery-goal-master"}},
                {MasteryGoal::Required, {"掌握", "mastery-goal-required"}},
                {MasteryGoal::Familiar, {"了解", "mastery-goal-familiar"}},
            };
        const auto& mark = goal_marks.at(goal);
        auto* badge = Gtk::make_managed<Gtk::Label>(mark.first);
        badge->add_css_class("lesson-tab-goal");
        badge->add_css_class(mark.second);
        badge->set_tooltip_text("掌握目标：" + mastery_goal_label(goal));
        row->append(*badge);
    }

    auto* dot = Gtk::make_managed<Gtk::Label>("●");
    dot->add_css_class("lesson-tab-dot");
    dot->add_css_class(mastery_tier(average_mastery));
    dot->set_tooltip_text(
        average_mastery <= 0.0
            ? string("尚未开始")
            : "平均熟练度 " + to_string(static_cast<int>(average_mastery + 0.5))
                  + " / 5");
    row->append(*dot);

    return row;
}

void TypeSemanticsLessonPage::open_experiment(const string& subchapter_name) {
    const auto& topic = topic_by_name(m_chapter, subchapter_name);
    if (m_on_experiment_requested) {
        m_on_experiment_requested(
            {.function_id = topic.function_id,
             .title = topic.title,
             .description = topic.description,
             .source_path = topic.source,
             .member_name = topic.name},
            false);
    }
}
