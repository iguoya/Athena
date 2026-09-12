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
    const map<string, int>& mastery_by_id,
    function<void(const ExperimentSelection&, bool)> on_experiment_requested,
    function<bool(const string&, int)> on_mastery_recorded)
    : m_chapter(chapter),
      m_on_experiment_requested(std::move(on_experiment_requested)),
      m_on_mastery_recorded(std::move(on_mastery_recorded)) {
    auto* init_unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_learning_unit_host");
    auto* run_button =
        builder->get_widget<Gtk::Button>("type_semantics_run_button");
    m_section_notebook = builder->get_widget<Gtk::Notebook>(
        "type_semantics_section_notebook");
    m_page_title = builder->get_widget<Gtk::Label>("type_semantics_page_title");
    auto* outline_roadmap_host =
        builder->get_widget<Gtk::Box>("ts_outline_roadmap_host");
    auto* guide_roadmap_host =
        builder->get_widget<Gtk::Box>("ts_guide_roadmap_host");
    m_value_matrix = builder->get_widget<Gtk::DrawingArea>("ts_vc_matrix");
    m_value_result_title =
        builder->get_widget<Gtk::Label>("ts_vc_result_title");
    m_value_result_detail =
        builder->get_widget<Gtk::Label>("ts_vc_result_detail");
    auto* value_unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_value_unit_host");

    auto* deduction_unit_host = builder->get_widget<Gtk::Box>(
        "type_semantics_deduction_unit_host");
    auto* deduction_variant_host = builder->get_widget<Gtk::Box>(
        "type_semantics_deduction_variant_host");
    auto* enum_unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_enum_unit_host");
    auto* cast_unit_host =
        builder->get_widget<Gtk::Box>("type_semantics_cast_unit_host");
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
    if (!init_unit_host || !run_button || !m_page_title
        || !m_section_notebook || !outline_roadmap_host
        || !guide_roadmap_host || !m_value_matrix
        || !m_value_result_title || !m_value_result_detail || !value_unit_host || !deduction_unit_host
        || !deduction_variant_host || !enum_unit_host || !cast_unit_host
        || !m_deduction_graph
        || !m_anim_status
        || !m_anim_note || !m_anim_playpause || !anim_prev || !anim_next
        || !anim_reset) {
        throw runtime_error("Failed to load TypeSemantics lesson Blueprint");
    }

    // 教案内嵌的静态 SVG 图与手册共享同一批资产（resources/articles/cpp/images/），
    // 打包进 /app 前缀的 GResource；结构留在 Blueprint，这里只填图源。
    const vector<pair<const char*, const char*>> lesson_figures = {
        {"ts_init_forms_figure", "/app/articles/cpp/images/init_forms.svg"},
        {"ts_auto_selection_figure",
         "/app/articles/cpp/images/auto_selection_flow.svg"},
        {"ts_lifetime_figure",
         "/app/articles/cpp/images/object_lifetime_timeline.svg"},
        {"ts_outline_model_figure",
         "/app/articles/cpp/images/type_semantics_model.svg"},
        {"ts_outline_loop_figure",
         "/app/articles/cpp/images/type_semantics_loop.svg"},
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

    // enum class 是策略节：正文让读者在三个情境里自己选，这里只用一道确认题
    // 收住最常被误解的边界——它挡的是隐式转换，不是显式转换。
    add_learning_unit(
        *enum_unit_host,
        LearningUnit{
            .id = "enum_explicit_cast_boundary",
            .heading = "",
            .claim = "作用域枚举挡住的是意外的隐式转换，不是你自己写下的显式转换。",
            .question =
                "FileState 只有 closed 和 open。static_cast<FileState>(42) 会怎样？",
            .choices = {
                "编译失败，42 不是合法的 FileState",
                "编译通过，得到一个不在枚举列表里的值",
                "编译通过，自动截断成 open",
            },
            .correct_choice = 1,
            .feedback = "编译通过。static_cast 是你明确写下的意图，编译器照做；得到的值不在 closed / open 之列，之后拿它 switch 或索引都不再受保护。所以从协议字节、配置文件这类外部数据转进枚举时，范围检查得你自己做。",
            .follow_up = "实验里的显式转换是反着来的——从枚举取底层值，那个方向永远安全。",
            .experiment_function_id = function_id_of(m_chapter, "enum_class"),
        },
        "enum_class");

    // 类型转换同样是策略节：三个片段让读者自己选，这里只收住最容易混的一点
    // ——const_cast 改的是访问路径，不是对象本身。
    add_learning_unit(
        *cast_unit_host,
        LearningUnit{
            .id = "const_cast_on_real_const_object",
            .heading = "",
            .claim = "const_cast 去掉的是访问路径上的 const，它管不了对象本来是什么。",
            .question =
                "const int fixed = 7; 之后用 const_cast 去掉限定再写入，会怎样？",
            .choices = {
                "编译失败，编译器会拦住对 const 对象的写入",
                "编译通过，fixed 被改成新值",
                "编译通过，但写入是未定义行为，结果不可依赖",
            },
            .correct_choice = 2,
            .feedback = "编译通过——const_cast 就是在告诉编译器「这个前提我担保」，它不再检查。但 fixed 本身定义为 const，写入它是未定义行为：可能改了、可能没改、可能整段代码被优化成别的样子。实验里的 const_cast 之所以安全，是因为那个对象本来就是可写的 int，只是经由一条只读路径访问。",
            .follow_up = "回到实验源码，确认被改的那个对象是怎么定义的——这个区别决定了同一行代码是安全还是未定义。",
            .experiment_function_id = function_id_of(m_chapter, "cast"),
        },
        "cast");

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

    // 标签顺序必须与 type_semantics_lesson.blp 中 Notebook 页顺序一致，
    // 而两者都服从教学大纲给出的推荐顺序——它就是知识点 requires 关系的拓扑序。
    // 大纲是方向决策层：页面顺序跟着它改，不是反过来。
    m_section_tabs = {
        {"本章导览", {}},
        {"教学大纲", {}},
        {"初始化", {"initialization"}},
        {"对象生命周期", {"object_lifetime"}},
        {"类型推导", {"auto_deduction"}},
        {"enum class", {"enum_class"}},
        {"类型转换", {"cast"}},
        {"值类别", {"value_category"}},
        // decltype 取类型的规则要用值类别说明，所以从「类型推导」拆出来排在最后。
        {"decltype", {"decltype_deduction"}},
    };
    // 四个表达式牵涉同一个对象 value，落在三个不同格子——「同一对象、不同表达式、
    // 不同值类别」是这一节最要紧的对照，所以做成可切换而不是一张静态表。
    const vector<tuple<const char*, ValueCategory, const char*>> value_buttons = {
        {"ts_vc_expr_named", ValueCategory::LValue, "value"},
        {"ts_vc_expr_move", ValueCategory::XValue, "std::move(value)"},
        {"ts_vc_expr_calc", ValueCategory::PRValue, "value + 0"},
        {"ts_vc_expr_named_rref", ValueCategory::LValue, "具名的 r"},
    };
    for (const auto& [widget_id, category, expression] : value_buttons) {
        auto* button = builder->get_widget<Gtk::Button>(widget_id);
        if (button == nullptr) {
            throw runtime_error(
                string("Missing TypeSemantics value button: ") + widget_id);
        }
        button->signal_clicked().connect([this, category, expression]() {
            select_value_expression(category, expression);
        });
    }
    m_value_matrix->set_draw_func(
        [this](const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) {
            draw_value_matrix(cr, width, height);
        });

    add_learning_unit(
        *value_unit_host,
        LearningUnit{
            .id = "named_rvalue_reference_is_lvalue",
            .heading = "",
            .claim = "「类型是右值引用」和「表达式是什么值类别」是两个问题。",
            .question =
                "int&& r = std::move(value); 之后把 r 传给一组重载，选中哪一个？",
            .choices = {
                "选中 int&& 那一版，因为 r 的类型是右值引用",
                "选中 int& 那一版，因为表达式 r 是左值",
                "有歧义，编译不过",
            },
            .correct_choice = 1,
            .feedback = "选中左值那一版。r 有名字、能取地址、能反复访问同一个对象——它是个左值，尽管它的类型写作 int&&。想让它继续以右值身份传下去，得再写一次 std::move(r)。转发时漏掉这一步，是最常见的一类性能问题。",
            .follow_up = "回到实验输出，对照具名表达式和 std::move 各自选中了哪一版。",
            .experiment_function_id = function_id_of(m_chapter, "value_category"),
        },
        "value_category");

    // 两张图共用 render/roadmap_view：同一批数据，各自编码不同维度。
    const auto open_section = [this](const string& name) {
        for (size_t index = 0; index < m_section_tabs.size(); ++index) {
            const auto& names = m_section_tabs[index].subchapter_names;
            if (find(names.begin(), names.end(), name) != names.end()) {
                // 跳到讲这个知识点的标签，而不是直接开实验——图的作用是指路。
                m_section_notebook->set_current_page(static_cast<int>(index));
                return;
            }
        }
    };
    m_outline_roadmap = make_unique<RoadmapView>(
        m_chapter,
        RoadmapView::Options{
            .color_by = RoadmapView::ColorBy::MasteryGoal,
            .show_goal_text = false,
            .show_progress = true},
        open_section);
    outline_roadmap_host->append(m_outline_roadmap->widget());

    m_guide_roadmap = make_unique<RoadmapView>(
        m_chapter,
        RoadmapView::Options{
            .color_by = RoadmapView::ColorBy::Difficulty,
            .show_goal_text = true,
            .show_progress = true},
        open_section);
    guide_roadmap_host->append(m_guide_roadmap->widget());
    m_outline_roadmap->set_mastery(mastery_by_id);
    m_guide_roadmap->set_mastery(mastery_by_id);

    m_section_notebook->signal_switch_page().connect(
        [this](Gtk::Widget*, guint index) {
            apply_page_title(static_cast<int>(index));
        });
    apply_page_title(m_section_notebook->get_current_page());

    build_checkpoints(builder);

    apply_tab_labels(mastery_by_id);
}



// 随堂考核题库。按 ADR 0028 的教学目标和大纲「回顾时尤其检查这些误区」出题：
// 考的是判断，不是记忆——每题都能用本节的实验跑出证据来对照。
void TypeSemanticsLessonPage::build_checkpoints(
    const Glib::RefPtr<Gtk::Builder>& builder) {
    const auto host = [&builder](const char* id) -> Gtk::Box* {
        return builder->get_widget<Gtk::Box>(id);
    };

    if (auto* box = host("type_semantics_init_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "initialization",
            .intro = "覆盖本节讲过的四种写法、两处边界和常见误区。答完按正确率评定"
                     "熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "初始化和\"先创建对象、再赋一个值给它\"是同一回事吗？",
                 .choices = {"是，只是说法不同",
                             "不是：对象从生命周期第一刻起就按某条规则取得初始状态",
                             "取决于类型是否有构造函数"},
                 .correct_choice = 1,
                 .explain = "对象没有\"先存在但还没有状态\"的阶段。初始状态由你写下的"
                            "初始化形式选中的那条规则决定——选错了，编译器未必拦你。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "double source = 3.75; 写 int value{source}; 结果是？",
                 .choices = {"value == 3", "value == 4", "编译错误", "未定义行为"},
                 .correct_choice = 2,
                 .explain = "花括号禁止窄化转换，在编译期直接拒绝。这里根本没有运行结果——"
                            "它是编译期规则，不是某个运行时输出。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "同样的 3.75，改写成 int value(source); 呢？",
                 .choices = {"编译错误", "value == 3，小数部分被丢弃",
                             "value == 4", "未定义行为"},
                 .correct_choice = 1,
                 .explain = "圆括号允许这次窄化，代价是小数部分被截断，而且没有任何提示。"
                            "确实接受截断时才用它——把这个决定写在明处。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "class Distance { explicit Distance(int); }; 下面哪一行编译不过？",
                 .choices = {"Distance a{10};", "Distance b = 10;",
                             "两行都不过", "两行都能过"},
                 .correct_choice = 1,
                 .explain = "explicit 切断的是隐式转换路径，也就是拷贝初始化；"
                            "显式写出意图的直接初始化 Distance a{10} 仍然成立。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "函数里写 int a{}; 和 int b;，两者有什么区别？",
                 .choices = {"没有区别，都是 0",
                             "a 一定是 0；b 未初始化，读它是未定义行为",
                             "a 未初始化；b 是 0", "都未初始化"},
                 .correct_choice = 1,
                 .explain = "普通局部变量不会自动清零。想要零就写 int a{}——"
                            "读一个没写过的变量\"看看它碰巧是几\"不是实验，是未定义行为。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "std::vector<int> v{3, 0}; 和 std::vector<int> v(3, 0); 分别得到什么？",
                 .choices = {"都是三个 0", "都是 {3, 0} 两个元素",
                             "前者两个元素 {3,0}，后者三个 0",
                             "前者三个 0，后者两个元素"},
                 .correct_choice = 2,
                 .explain = "花括号会优先匹配 initializer_list 构造函数。这是\"花括号更安全\""
                            "这条经验的一个例外：对容器来说，两种括号表达的是不同意图。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "把花括号和圆括号当成风格偏好、随手互换，主要的风险是什么？",
                 .choices = {"没有风险，只是团队习惯",
                             "它们在窄化检查上规则不同，换一下就可能把编译错误变成静默截断",
                             "花括号更慢", "圆括号不支持自定义类型"},
                 .correct_choice = 1,
                 .explain = "同样一行代码，花括号让编译器替你把关，圆括号让你自己承担后果。"
                            "这是语义差别，不是排版偏好。",
                 .difficulty = 1, .goal = QuestionGoal::Master},
                {.stem = "要表达\"这个值必须无损地进入目标类型\"，应该选哪种写法？",
                 .choices = {"圆括号 ()", "花括号 {}", "等号赋值", "都行"},
                 .correct_choice = 1,
                 .explain = "花括号把\"会不会丢信息\"的判断交给编译器，在编译期就挡住。"
                            "需要调用者明确接受截断时才退回圆括号。",
                 .difficulty = 1, .goal = QuestionGoal::Required},
            }});
    }

    if (auto* box = host("type_semantics_lifetime_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "object_lifetime",
            .intro = "覆盖三种结束时点、寿命延长规则及其两条边界。答完按正确率评定"
                     "熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "一个有名字的局部对象，什么时候结束？",
                 .choices = {"函数返回时", "离开它所在的那对花括号时",
                             "最后一次被使用之后", "没有引用指向它时"},
                 .correct_choice = 1,
                 .explain = "块作用域说了算，而块不一定是函数体——一对花括号就够。"
                            "这也是需要缩短某个对象寿命时的常用手段。",
                 .difficulty = 1, .goal = QuestionGoal::Master},
                {.stem = "一个没有名字的临时对象（比如函数返回值、隐式转换的中间结果），活到什么时候？",
                 .choices = {"所在语句的分号处", "所在函数结束",
                             "所在块结束", "下一次赋值时"},
                 .correct_choice = 0,
                 .explain = "临时对象在完整表达式结束时销毁，也就是分号处。它经常出现在"
                            "你没有写出它的地方，所以要有意识地去找。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "把一个临时对象直接绑到 const 引用上，会发生什么？",
                 .choices = {"引用当场悬垂", "临时对象活到这个引用自己的作用域结束",
                             "编译错误", "临时对象被复制一份"},
                 .correct_choice = 1,
                 .explain = "这就是寿命延长规则，它让\"接住一个临时结果再多用几行\"成为可能。"
                            "但要记牢它的适用范围：只对直接绑定的那个临时对象生效。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "把临时对象内部的某个成员绑到 const 引用上（不是绑整个临时对象），呢？",
                 .choices = {"成员也被延长", "临时对象仍在分号处结束，引用当场悬垂",
                             "编译错误", "整个临时对象被延长"},
                 .correct_choice = 1,
                 .explain = "延长的是那个临时对象本身，不是从它取出来的成员。"
                            "这条边界很容易被\"const 引用能延长寿命\"这句话盖过去。",
                 .difficulty = 4, .goal = QuestionGoal::Required},
                {.stem = "函数把返回类型写成引用，返回自己的局部对象，调用方拿到什么？",
                 .choices = {"有效引用，寿命被延长了", "有效引用，因为发生了复制",
                             "失效引用，访问它是未定义行为", "编译错误"},
                 .correct_choice = 2,
                 .explain = "延长规则不跨函数边界。把返回类型写成引用不会让局部对象多活一秒——"
                            "要把结果带出函数，返回值本身就够了。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "同一个块里先后构造了 a、b、c 三个局部对象，离开块时析构顺序是？",
                 .choices = {"a、b、c", "c、b、a", "不确定", "取决于类型"},
                 .correct_choice = 1,
                 .explain = "按与构造相反的顺序析构。这条顺序是确定的，实验里的探针对象"
                            "在构造和析构时各打印一行，可以直接看到。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "只要还有引用指向某个对象，它就不会被销毁——这个说法对吗？",
                 .choices = {"对", "不对：三种结束时点都不受\"有没有人还在引用\"影响"},
                 .correct_choice = 1,
                 .explain = "引用不会让对象多活。C++ 里对象的寿命由作用域和规则决定，"
                            "不是由引用计数决定——这一点和带 GC 的语言根本不同。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "访问一个已经结束的对象，最麻烦的地方在哪？",
                 .choices = {"一定会崩溃，容易发现",
                             "是未定义行为：可能照常运行一次，换台机器或换优化级别就变",
                             "编译器会警告", "只影响性能"},
                 .correct_choice = 1,
                 .explain = "\"跑一次没事\"不能证明没问题。这类错误的代价正在于它不稳定——"
                            "所以要靠规则判断有效期，而不是靠运行一次来确认。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
            }});
    }

    if (auto* box = host("type_semantics_deduction_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "auto_deduction",
            .intro = "覆盖三种访问意图、const 的作用范围，以及 auto 的两条边界。"
                     "答完按正确率评定熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "int original = 42; auto copy = original; 之后 copy = 7，original 变成多少？",
                 .choices = {"7", "42", "未定义", "编译错误"},
                 .correct_choice = 1,
                 .explain = "auto 按值推导，copy 是另一个独立的整数对象。"
                            "即使右边写的是某个引用的名字，按值推导也不会把 copy 变成引用。",
                 .difficulty = 1, .goal = QuestionGoal::Master},
                {.stem = "auto& alias = original; 之后 alias = 99，发生了什么？",
                 .choices = {"新建了一个整数，值为 99",
                             "original 变成 99，没有新建整数对象",
                             "alias 变 99，original 不变", "编译错误"},
                 .correct_choice = 1,
                 .explain = "alias 是 original 的另一个名字，不是第二个整数容器。"
                            "判断会不会互相影响的办法：先数有几个对象，再看每个名字关联谁。",
                 .difficulty = 1, .goal = QuestionGoal::Master},
                {.stem = "const auto& view = original; 之后写 view = 20 会怎样？",
                 .choices = {"original 变成 20", "view 变成 20，original 不变",
                             "编译错误：不能通过 view 赋值", "运行期报错"},
                 .correct_choice = 2,
                 .explain = "const 引用是一条只读的访问路径。这是编译期就被拒绝的写法，"
                            "不是运行时能打印出来的现象。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "有了 const auto& view = original 之后，original 本身还能被修改吗？",
                 .choices = {"不能，它被 view 锁住了",
                             "能：const 限制的只是 view 这一条访问路径",
                             "取决于编译器", "只能通过 view 修改"},
                 .correct_choice = 1,
                 .explain = "const 修饰的是这一条访问路径，不会把原对象整个冻结。"
                            "通过 original 本身或别的可写别名赋值，view 读到的值就会跟着变。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "两个整数对象此刻数值都是 42，能否据此认为它们是同一个对象？",
                 .choices = {"能", "不能：数值相等和指向同一对象是两件事"},
                 .correct_choice = 1,
                 .explain = "数值刚好相同说明不了对象相同。copy 和 original 曾经同为 42，"
                            "那只是因为一个用另一个的值做了初始化。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "把一个持有指针或共享所有权的对象写成 auto x = y;，x 一定和 y 完全独立吗？",
                 .choices = {"一定独立，auto 会做深拷贝",
                             "不一定：复制的可能只是指针或所有权句柄，底层资源仍然共享"},
                 .correct_choice = 1,
                 .explain = "auto 只决定\"按值还是按引用\"，不保证深拷贝。本节的对象图只解释"
                            "普通 int 这个例子，不能推广成所有类型的内存图。",
                 .difficulty = 4, .goal = QuestionGoal::Required},
                {.stem = "想修改容器里已有的某个元素，写成 auto element = container[i]; element = 新值; 会怎样？",
                 .choices = {"容器里的元素被改了",
                             "改的是复制出来的副本，容器没变",
                             "编译错误", "取决于容器类型"},
                 .correct_choice = 1,
                 .explain = "这正是本节判断带到容器里的样子：要改已有元素就不能把它复制出来，"
                            "该写 auto&；反过来，想要一份独立数据用于试改，也别意外留下可写别名。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "把类型交给编译器推导之后，还需要自己表达什么？",
                 .choices = {"不用了，编译器全包",
                             "仍要表达意图：要一份值，还是要继续访问原来的对象",
                             "只需要关心性能", "只需要关心可读性"},
                 .correct_choice = 1,
                 .explain = "推导省掉的是重复书写，不是决定。值、可写别名、只读访问这三种意图"
                            "仍然只能由你在声明里写出来。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
            }});
    }

    if (auto* box = host("type_semantics_enum_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "enum_class",
            .intro = "覆盖两种写法的差别、三条判据、要付的代价和值域边界。"
                     "答完按正确率评定熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "用 const int kClosed = 0; kOpen = 1; 加 void report(int) 来表示文件状态，"
                         "编译器会放行下面哪些写法？",
                 .choices = {"只有 report(kClosed) 和 report(kOpen)",
                             "report(42)、别组常量 report(kRed)、以及 state + 1 都放行",
                             "只放行 state + 1", "都不放行"},
                 .correct_choice = 1,
                 .explain = "签名说的是\"给我一个整数\"，那三行就都合法。它们在语义上全是错的，"
                            "编译器却一件也挡不住。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "enum class FileState { closed, open }; 写 int n = FileState::open;",
                 .choices = {"编译通过，n == 1", "编译错误", "编译通过但有警告"},
                 .correct_choice = 1,
                 .explain = "作用域枚举不隐式转成整数——这正是它要挡住的误用。"
                            "确实需要底层值时用 static_cast 显式写出来。",
                 .difficulty = 1, .goal = QuestionGoal::Required},
                {.stem = "按本节的三条判据，哪一组条件最值得给一组值独立类型？",
                 .choices = {"值很多、需要排序、性能敏感",
                             "要跨接口传递、值没有算术意义、怕和别处的同类整数混淆",
                             "只在一个函数内部区分几个分支",
                             "需要按位组合"},
                 .correct_choice = 1,
                 .explain = "三条同时成立时收益最明显。只满足一条时未必值得——函数内部临时"
                            "区分几个分支，裸整数或普通枚举也够用。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "选择 enum class 要付出的代价是什么？",
                 .choices = {"运行更慢、占用更多内存",
                             "取底层值必须显式 static_cast、不能直接当下标、位运算要自己重载",
                             "不能用于 switch", "不能指定底层类型"},
                 .correct_choice = 1,
                 .explain = "这些不是缺陷，是换来严格检查所付的价钱。划算的做法是把这些显式转换"
                            "收在协议解析、表索引这样明确的一两处。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "要表示可组合的权限位（读、写、执行，需要按位取并），enum class 合适吗？",
                 .choices = {"合适，它最安全",
                             "不方便：默认不支持按位运算，而且组合出的值本来就不在列出的取值里",
                             "合适，但要加 static_cast", "只能用 enum class"},
                 .correct_choice = 1,
                 .explain = "这正是它代价所在的地方。不是所有整数常量集合都该改成 enum class——"
                            "判据不成立时，硬套只会增加样板代码。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "enum class FileState { closed, open }; 写 static_cast<FileState>(42) 会怎样？",
                 .choices = {"编译错误", "运行期抛异常",
                             "能编译，得到一个不在 closed / open 里的值",
                             "自动截断到合法值"},
                 .correct_choice = 2,
                 .explain = "作用域枚举拦得住隐式转换，拦不住你显式转进来的越界值。所以从协议"
                            "字节、配置文件、用户输入转进枚举时，范围检查要自己在转换点做。",
                 .difficulty = 4, .goal = QuestionGoal::Required},
                {.stem = "enum class FileState : unsigned char { ... } 里的 : unsigned char 是什么意思？",
                 .choices = {"限制成员个数不超过 255", "指定底层类型",
                             "让它可以隐式转成 unsigned char", "没有实际作用"},
                 .correct_choice = 1,
                 .explain = "指定底层类型，实验里可以看到它确实就是你指定的那个。"
                            "这在需要控制存储大小或与协议字段对齐时有用。",
                 .difficulty = 2, .goal = QuestionGoal::Familiar},
                {.stem = "如果这组值的主要用途就是直接索引一张查找表，还值得用 enum class 吗？",
                 .choices = {"绝对值得", "绝对不值得",
                             "可以用但要想清楚：每次索引都要 static_cast，收益会被样板代码抵消一部分"},
                 .correct_choice = 2,
                 .explain = "答案不是清一色的\"用\"。折中做法是保留 enum class，再配一个集中的"
                            "转换函数，把样板代码收在一处。",
                 .difficulty = 3, .goal = QuestionGoal::Familiar},
            }});
    }

    if (auto* box = host("type_semantics_cast_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "cast",
            .intro = "覆盖三类隐式转换、四种命名转换各自的承诺、检查发生在哪一层，"
                     "以及三个判断情境。答完按正确率评定熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "-1 < 1u 的结果是什么？",
                 .choices = {"true", "false", "编译错误", "未定义行为"},
                 .correct_choice = 1,
                 .explain = "比较之前 -1 先被转成一个极大的无符号数。写的人以为在比较大小，"
                            "实际比较的是转换之后的两个值——循环条件里最经典的一类 bug。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "把 300 存进 unsigned char，以及让有符号整数溢出，两者性质一样吗？",
                 .choices = {"一样，都是未定义行为",
                             "不一样：无符号是良定义的取模（得到 44），有符号溢出才是未定义行为",
                             "一样，都是良定义的", "都会编译错误"},
                 .correct_choice = 1,
                 .explain = "同样看不见的一次转换，有符号和无符号的后果性质完全不同。"
                            "无符号回绕是规定好的，有符号溢出编译器可以据此做任意假设。",
                 .difficulty = 4, .goal = QuestionGoal::Required},
                {.stem = "static_cast 这句话的承诺是什么？",
                 .choices = {"这次转换一定安全",
                             "我相信这两个类型之间存在明确定义的转换；关系由编译期检查，后果我承担",
                             "请在运行期帮我检查", "按位重新解读"},
                 .correct_choice = 1,
                 .explain = "编译期检查的是\"这层关系存不存在\"，不是\"值合不合理\"。"
                            "小数被截断这类后果，是写下它的人接手的。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "四种命名转换里，哪一种在运行期做检查？",
                 .choices = {"static_cast", "dynamic_cast", "const_cast",
                             "reinterpret_cast"},
                 .correct_choice = 1,
                 .explain = "它是唯一在运行期查的：转指针失败得到 nullptr，转引用失败抛 bad_cast。"
                            "代价是要求源类型是多态类型，并且要付运行期查询的开销。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "const_cast 改变的是什么？",
                 .choices = {"对象本身的可写性", "访问路径上的 const 限定",
                             "对象的类型", "对象的存储位置"},
                 .correct_choice = 1,
                 .explain = "它只改访问路径。如果对象原本就定义为 const，去掉限定再写入是"
                            "未定义行为——编译器不拦你，这个前提完全由你保证。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "四种命名转换按检查强度从严到松排，正确的顺序是？",
                 .choices = {"static_cast > dynamic_cast > const_cast > reinterpret_cast",
                             "dynamic_cast > static_cast > const_cast > reinterpret_cast",
                             "reinterpret_cast > const_cast > static_cast > dynamic_cast",
                             "四种一样强"},
                 .correct_choice = 1,
                 .explain = "选择原则很简单：能用检查更严的就不用更松的。写下哪一个，"
                            "就是在说明这次转换的前提由谁来保证。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "C 风格的 (int)x 属于上面哪一层？",
                 .choices = {"等价于 static_cast",
                             "依次尝试几种，选第一个说得通的——读代码的人看不出意图",
                             "等价于 reinterpret_cast", "编译器会报警告"},
                 .correct_choice = 1,
                 .explain = "看不出意图，也搜不出代码库里所有的危险转换。四种命名转换分开，"
                            "正是为了让意图留在代码里、能被检索。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "拿到一个 Shape*，想调用 Circle 特有的方法，该用哪种转换？",
                 .choices = {"static_cast，简单直接",
                             "dynamic_cast，并检查返回值",
                             "reinterpret_cast", "C 风格转换"},
                 .correct_choice = 1,
                 .explain = "你不确定它是不是 Circle，这正是运行期检查存在的理由。"
                            "static_cast 也能编译，但猜错时不会有任何提示。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "一个函数收 const 引用，你却想在函数里改它，最该做什么？",
                 .choices = {"用 const_cast 去掉限定", "改接口，不要转换",
                             "复制一份再改", "用 reinterpret_cast"},
                 .correct_choice = 1,
                 .explain = "函数签名承诺了\"我不改你的东西\"，const_cast 只是把违背承诺的事"
                            "藏起来；而且一旦调用方传来的真是 const 对象，写入就是未定义行为。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "代码里频繁出现各种转换，通常说明什么？",
                 .choices = {"代码很灵活", "类型设计没表达清楚意图",
                             "性能优化到位", "这是现代 C++ 的常态"},
                 .correct_choice = 1,
                 .explain = "该用独立类型的地方用了裸整数，该改接口的地方用了 const_cast。"
                            "最该先问的问题是\"这次转换能不能不做\"，然后才是\"该用哪种\"。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
            }});
    }

    if (auto* box = host("type_semantics_value_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "value_category",
            .intro = "覆盖两个判断问题、三类值类别，以及三处最容易踩的边界。"
                     "答完按正确率评定熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "判断一个表达式的值类别，要问的是哪两个问题？",
                 .choices = {"类型是什么、占多少字节",
                             "有没有身份（能否取地址、之后还能否访问同一对象）、能不能被移动",
                             "是不是 const、是不是引用",
                             "在栈上还是堆上"},
                 .correct_choice = 1,
                 .explain = "有身份不可移动是左值，有身份且可移动是将亡值，无身份可移动是纯右值。"
                            "第四种组合没有意义，所以只有三类。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "值类别是谁的属性？",
                 .choices = {"对象的属性", "表达式的属性", "类型的属性", "变量名的属性"},
                 .correct_choice = 1,
                 .explain = "同一个对象出现在不同表达式里，值类别可以完全不同。这一点没分清，"
                            "后面关于引用绑定和重载的判断都会跟着错。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "int&& r = std::move(value); 之后，单独写出的表达式 r 是什么值类别？",
                 .choices = {"将亡值，因为 r 的类型是右值引用",
                             "左值：它有名字、能取地址、能反复用",
                             "纯右值", "取决于上下文"},
                 .correct_choice = 1,
                 .explain = "\"r 的类型是右值引用\"和\"表达式 r 是什么值类别\"是两个问题。"
                            "实验里可以看到：具名的右值引用再传出去时，选中的是左值那一版重载。",
                 .difficulty = 4, .goal = QuestionGoal::Master},
                {.stem = "value + 0 这个表达式属于哪一类？",
                 .choices = {"左值", "将亡值", "纯右值"},
                 .correct_choice = 2,
                 .explain = "算出来就没了的中间结果，没有身份——不能取地址，也没法在后面"
                            "再访问\"同一个\"它。",
                 .difficulty = 2, .goal = QuestionGoal::Master},
                {.stem = "std::move(value) 这次调用本身做了什么？",
                 .choices = {"把 value 的资源搬走了", "把 value 置空",
                             "只是一次类型转换，把表达式变成将亡值",
                             "复制了一份 value"},
                 .correct_choice = 2,
                 .explain = "变的是\"重载时选哪个\"，不是内存里发生了什么。实验里能直接看到："
                            "std::move 之后选中了 string&&，而对象本身并没有被搬走。",
                 .difficulty = 3, .goal = QuestionGoal::Master},
                {.stem = "一个表达式是将亡值，是否意味着它指向的对象马上要销毁？",
                 .choices = {"是", "不是：将亡值说的是\"允许把资源搬走\"，不是\"对象即将消失\""},
                 .correct_choice = 1,
                 .explain = "value 在 std::move(value) 之后照样活到作用域结束。资源是否真被"
                            "搬走，取决于接收方选中了哪个重载、那个重载做了什么。",
                 .difficulty = 4, .goal = QuestionGoal::Master},
                {.stem = "把同一个 string 对象分别以具名表达式和 std::move 的形式传给一组重载，"
                         "选中的分别是哪一版？",
                 .choices = {"都是 string&", "都是 string&&",
                             "具名时选 string&，std::move 之后选 string&&",
                             "取决于编译器"},
                 .correct_choice = 2,
                 .explain = "这正是值类别影响重载决议的直接证据，实验里一跑就能看到。"
                            "只读表达式则会落到 const string& 那一版。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "这一节要求掌握到什么程度就够了？",
                 .choices = {"连引用折叠和完美转发一起吃透",
                             "能判断三类、能说明它影响哪种绑定",
                             "背下所有标准条文", "会用 std::move 就行"},
                 .correct_choice = 1,
                 .explain = "规则密度高的部分留到写模板时再回来——那时你会需要这套判断，"
                            "现在不会。先把三类分清、把绑定关系说清楚。",
                 .difficulty = 1, .goal = QuestionGoal::Familiar},
            }});
    }

    if (auto* box = host("type_semantics_decltype_checkpoint_host")) {
        add_checkpoint(*box, Checkpoint{
            .knowledge_id = "decltype_deduction",
            .intro = "覆盖名字与表达式两条规则、按值类别取类型的对应关系，以及它和 auto "
                     "的分工。答完按正确率评定熟练度并记入学习进度，可以重做。",
            .questions = {
                {.stem = "int value = 0; decltype(value) 是什么类型？",
                 .choices = {"int", "int&", "int&&", "const int"},
                 .correct_choice = 0,
                 .explain = "未加括号的名字，取的是这个实体的声明类型。value 声明成 int，"
                            "答案就是 int。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "同一个 value，decltype((value)) 呢？",
                 .choices = {"int", "int&", "int&&", "编译错误"},
                 .correct_choice = 1,
                 .explain = "多一层括号之后它不再是实体名，而是一个表达式，于是进入表达式规则："
                            "具名左值表达式按值类别取类型，得到 int&。",
                 .difficulty = 4, .goal = QuestionGoal::Familiar},
                {.stem = "对一般表达式，decltype 怎样保留值类别？",
                 .choices = {"一律去掉引用，得到 T",
                             "左值得 T&，将亡值得 T&&，纯右值得 T",
                             "一律得 T&", "取决于编译器"},
                 .correct_choice = 1,
                 .explain = "它用引用类型来编码值类别，所以 std::move(x) 这种将亡值会得到 T&&，"
                            "而 x + 0 这种纯右值得到 T。",
                 .difficulty = 4, .goal = QuestionGoal::Familiar},
                {.stem = "decltype 和 auto 问的是同一个问题吗？",
                 .choices = {"是，只是写法不同",
                             "不是：auto 问\"在这里声明怎样的变量\"，decltype 问"
                             "\"这个名字或表达式按语言规则具有什么类型\"",
                             "decltype 只是 auto 的旧写法"},
                 .correct_choice = 1,
                 .explain = "auto 是站在\"新变量\"的角度推导，会丢掉引用和顶层 const；"
                            "decltype 是站在\"实体或表达式\"的角度回答，原样保留。",
                 .difficulty = 3, .goal = QuestionGoal::Required},
                {.stem = "什么场合最需要 decltype？",
                 .choices = {"任何能少写类型名的地方",
                             "需要让一处声明的类型精确跟随某个名字或表达式时，比如泛型代码里的返回类型",
                             "所有初始化语句", "性能敏感的代码"},
                 .correct_choice = 1,
                 .explain = "写得出具体类型的地方用 auto 就够了。decltype 的价值在类型写不出来"
                            "的场合——依赖模板参数的返回类型、要保留引用性的转发。",
                 .difficulty = 2, .goal = QuestionGoal::Required},
                {.stem = "本节给出的两条规则，覆盖了 decltype 的全部情况吗？",
                 .choices = {"是，全部",
                             "不是：结构化绑定等特殊规则另有约定，这里讲的是普通名字与表达式"},
                 .correct_choice = 1,
                 .explain = "知道规则有边界，比背下几条更要紧——遇到特殊场景时要意识到"
                            "需要回去查，而不是照着这两条硬推。",
                 .difficulty = 2, .goal = QuestionGoal::Familiar},
            }});
    }

}

CheckpointView& TypeSemanticsLessonPage::add_checkpoint(
    Gtk::Box& host, Checkpoint data) {
    // 题目里写的是成员函数短名，落库要用完整函数 ID（分类.章节.知识点）。
    const auto& topic = topic_by_name(m_chapter, data.knowledge_id);
    data.knowledge_id = topic.function_id;
    const string verify_name = topic.name;
    if (data.experiment_function_id.empty()) {
        data.experiment_function_id = topic.function_id;
    }
    m_checkpoint_data.push_back(make_unique<Checkpoint>(std::move(data)));
    auto view = make_unique<CheckpointView>(
        *m_checkpoint_data.back(),
        m_on_mastery_recorded,
        [this, verify_name](const string&) { open_experiment(verify_name); });
    host.append(view->widget());
    m_checkpoint_views.push_back(std::move(view));
    return *m_checkpoint_views.back();
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

void TypeSemanticsLessonPage::select_value_expression(
    ValueCategory category, const string& expression) {
    m_value_selection = category;

    struct Explanation {
        const char* name;
        const char* binding;
        const char* why;
    };
    static const map<ValueCategory, Explanation> table = {
        {ValueCategory::LValue,
         {"左值",
          "能绑到 int& 和 const int&，绑不到 int&&",
          "它有身份：能取地址，后面还能再访问同一个对象；没有任何东西说它可以被搬走。"}},
        {ValueCategory::XValue,
         {"将亡值",
          "能绑到 int&& 和 const int&，绑不到 int&",
          "std::move 只是把它标成「可以搬走」——身份还在（说的仍是同一个对象），但重载时会优先选右值那一版。对象本身此刻并没有被动过。"}},
        {ValueCategory::PRValue,
         {"纯右值",
          "能绑到 int&& 和 const int&，绑不到 int&",
          "算出来就没了：没有名字、取不到地址，后面也没法再访问「同一个」它。"}},
        {ValueCategory::None, {"", "", ""}},
    };

    const auto& explanation = table.at(category);
    if (m_value_result_title != nullptr) {
        m_value_result_title->set_text(
            expression + " 是" + explanation.name);
    }
    if (m_value_result_detail != nullptr) {
        m_value_result_detail->set_text(
            string(explanation.binding) + "。" + explanation.why);
    }
    if (m_value_matrix != nullptr) {
        m_value_matrix->queue_draw();
    }
}

void TypeSemanticsLessonPage::draw_value_matrix(
    const Cairo::RefPtr<Cairo::Context>& cr, int width, int height) const {
    const double w = static_cast<double>(width);
    const double cell_w = min(230.0, (w - 150.0) / 2.0);
    const double cell_h = 74.0;
    const double left = 130.0;
    const double top = 54.0;

    // 轴标题：两个问题就是两个维度，先让它们各自可读，再看格子。
    draw_cairo_text(cr, "可以被移动吗", left + cell_w, 22.0, 13.0, kMuted, true, 0.5);
    draw_cairo_text(cr, "否", left + cell_w / 2.0, 42.0, 12.5, kMuted, false, 0.5);
    draw_cairo_text(cr, "是", left + cell_w * 1.5, 42.0, 12.5, kMuted, false, 0.5);
    draw_cairo_text(cr, "有身份吗", 60.0, top - 14.0, 13.0, kMuted, true, 0.5);
    draw_cairo_text(cr, "是", 60.0, top + cell_h / 2.0, 12.5, kMuted, false, 0.5);
    draw_cairo_text(cr, "否", 60.0, top + cell_h * 1.5 + 10.0, 12.5, kMuted, false, 0.5);

    struct Cell {
        ValueCategory category;
        const char* label;
        const char* example;
        double x;
        double y;
    };
    const vector<Cell> cells = {
        {ValueCategory::LValue, "左值", "value", left, top},
        {ValueCategory::XValue, "将亡值", "std::move(value)", left + cell_w, top},
        {ValueCategory::None, "（没有这一类）", "无身份又不可移动没有意义",
         left, top + cell_h + 10.0},
        {ValueCategory::PRValue, "纯右值", "value + 0", left + cell_w,
         top + cell_h + 10.0},
    };

    for (const auto& cell : cells) {
        const bool empty_cell = cell.category == ValueCategory::None;
        const bool selected = !empty_cell && cell.category == m_value_selection;
        ChartColor border = empty_cell ? ChartColor{0.85, 0.87, 0.89} : kMuted;
        ChartColor fill = empty_cell ? ChartColor{0.97, 0.97, 0.98}
                                     : ChartColor{0.99, 0.99, 1.0};
        if (selected) {
            border = kNameStroke;
            fill = kNameFill;
        }
        rounded_box(
            cr, cell.x, cell.y, cell_w - 10.0, cell_h, border, fill, empty_cell);
        draw_cairo_text(
            cr, cell.label, cell.x + (cell_w - 10.0) / 2.0, cell.y + 26.0, 14.0,
            empty_cell ? kMuted : kInk, !empty_cell, 0.5);
        draw_cairo_text(
            cr, cell.example, cell.x + (cell_w - 10.0) / 2.0, cell.y + 50.0, 12.0,
            kMuted, false, 0.5);
    }

    if (m_value_selection == ValueCategory::None) {
        draw_cairo_text(
            cr, "点上面任意一个表达式，看它落在哪一格", w / 2.0,
            static_cast<double>(height) - 14.0, 12.5, kMuted, false, 0.5);
    }
}

void TypeSemanticsLessonPage::refresh_progress(
    const map<string, int>& mastery_by_id) {
    m_outline_roadmap->set_mastery(mastery_by_id);
    m_guide_roadmap->set_mastery(mastery_by_id);
    apply_tab_labels(mastery_by_id);
}

void TypeSemanticsLessonPage::apply_page_title(int page_index) {
    // 页头以前写死成「类型与表达式 · 初始化」，切到别的标签也不变，读者会
    // 以为自己还在第一节。小节名跟着当前标签走，前两个标签不是知识点，
    // 只显示章节名。
    const string base = m_chapter.title;
    if (page_index < 0
        || page_index >= static_cast<int>(m_section_tabs.size())) {
        m_page_title->set_text(base);
        return;
    }
    const auto& section = m_section_tabs[static_cast<size_t>(page_index)];
    m_page_title->set_text(base + " · " + section.title);
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
