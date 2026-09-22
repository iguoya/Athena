#include "pocket_cube/pocket_cube.hpp"
#include "pocket_cube/view.h"

#include <gtkmm.h>

#include <algorithm>
#include <chrono>
#include <functional>
#include <memory>
#include <numbers>
#include <optional>
#include <vector>

using namespace std;

namespace {

string format_thousands(long long value) {
    string digits = to_string(value);
    string result;
    int count = 0;
    for (auto it = digits.rbegin(); it != digits.rend(); ++it) {
        if (count != 0 && count % 3 == 0) {
            result.push_back(',');
        }
        result.push_back(*it);
        ++count;
    }
    reverse(result.begin(), result.end());
    return result;
}

constexpr int kTurnAnimationMs = 400;
constexpr int kTurnAnimationFrameMs = 16;

// U/R/F 三个面在"状态空间"三组圆里各自对应哪一组——上（橙）=U、
// 左下（绿）=R、右下（紫）=F，见 view.h 的 RingAnimation 注释；这个
// 应用只穷举 U/R/F 三个面（见 state.h 的 next_move_set() 注释），
// 不会遇到其它面，所以不用处理 D/L/B。
int ring_group_for_face(Face face) {
    switch (face) {
    case Face::U: return 0;
    case Face::R: return 1;
    case Face::F: return 2;
    default: return -1;
    }
}

// rings_view/rings_animation_state 是可选的：只有"操作区"九个按钮
// （真正改状态的那九个）需要联动"状态空间"面板的圆环转动，"未来状态"
// 九宫格每格右下角的预览切换按钮只是本地展示开关、不代表真实发生的
// 转动，不传这两个参数（保持默认 nullptr）就行——同一个动画循环，
// 两边的进度（progress）算的是同一个数，天然同步，不需要维护两条
// 独立的计时器。
void play_turn_animation(
    Gtk::Widget* view_3d,
    shared_ptr<optional<TurnAnimation>> animation_state,
    Move move,
    bool reverse,
    function<void()> on_complete,
    Gtk::Widget* rings_view = nullptr,
    shared_ptr<optional<RingAnimation>> rings_animation_state = nullptr) {
    const FaceLayout layout = face_layout(move.face);
    const double target_degrees = turn_angle_degrees(move);
    const double start_degrees = reverse ? target_degrees : 0.0;
    const double end_degrees = reverse ? 0.0 : target_degrees;
    const int ring_group = ring_group_for_face(move.face);

    *animation_state =
        TurnAnimation{layout.normal_axis, layout.normal_sign, start_degrees};
    view_3d->queue_draw();
    if (rings_view && rings_animation_state && ring_group >= 0) {
        *rings_animation_state =
            RingAnimation{ring_group, start_degrees * std::numbers::pi / 180.0};
        rings_view->queue_draw();
    }

    const auto started = chrono::steady_clock::now();
    Glib::signal_timeout().connect(
        [animation_state, view_3d, started, start_degrees, end_degrees,
         on_complete, rings_view, rings_animation_state, ring_group]() -> bool {
            const double elapsed_ms = chrono::duration<double, milli>(
                                          chrono::steady_clock::now() - started)
                                          .count();
            const double progress = min(1.0, elapsed_ms / kTurnAnimationMs);
            const double current_degrees =
                start_degrees + (end_degrees - start_degrees) * progress;
            if (*animation_state) {
                (*animation_state)->current_degrees = current_degrees;
            }
            view_3d->queue_draw();
            if (rings_view && rings_animation_state && ring_group >= 0) {
                *rings_animation_state = RingAnimation{
                    ring_group, current_degrees * std::numbers::pi / 180.0};
                rings_view->queue_draw();
            }
            if (progress >= 1.0) {
                *animation_state = nullopt;
                if (rings_animation_state) {
                    *rings_animation_state = nullopt;
                }
                on_complete();
                return false;
            }
            return true;
        },
        kTurnAnimationFrameMs);
}

// 操作视角面板：只画 face 这一个面的 2x2 格子（make_cube_face_view()，
// 没有透视、不用拖拽），标题写清楚是哪个操作面——给"这个面现在是什么
// 颜色"这种只关心单个面的场景用，不是"转完之后会变成什么样"的预测。
Gtk::Widget* make_operation_face_panel(
    function<CubeState()> state_provider, Face face, const string& caption,
    vector<Gtk::Widget*>& redraw_targets) {
    auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
    box->set_hexpand(true);
    box->set_vexpand(true);
    box->set_halign(Gtk::Align::FILL);
    box->set_valign(Gtk::Align::FILL);
    box->set_margin(6);

    auto* view_face = make_cube_face_view(state_provider, face, 140, 140);
    view_face->set_hexpand(true);
    view_face->set_vexpand(true);
    box->append(*view_face);
    redraw_targets.push_back(view_face);

    auto label = Gtk::make_managed<Gtk::Label>(caption);
    label->add_css_class("caption");
    label->add_css_class("dim-label");
    label->set_halign(Gtk::Align::CENTER);
    box->append(*label);

    auto frame = Gtk::make_managed<Gtk::Frame>();
    frame->set_hexpand(true);
    frame->set_vexpand(true);
    frame->add_css_class("panel-frame");
    frame->set_child(*box);
    return frame;
}

void wire_window(const Glib::RefPtr<Gtk::Builder>& builder) {
    auto reset_button = builder->get_widget<Gtk::Button>("practice_reset_button");
    auto current_host = builder->get_widget<Gtk::Box>("practice_cube_current_host");
    auto next_grid_host =
        builder->get_widget<Gtk::Box>("practice_cube_next_grid_host");
    auto state_space_host =
        builder->get_widget<Gtk::Box>("practice_state_space_host");
    auto operations_host =
        builder->get_widget<Gtk::Box>("practice_operations_host");

    Gtk::Widget* rings_view = nullptr;
    auto rings_animation = make_shared<optional<RingAnimation>>();
    if (state_space_host) {
        rings_view = make_state_space_rings_view(
            kCubeStateSpaceSizeIgnoringOrientation, 320,
            [rings_animation] { return *rings_animation; });
        state_space_host->append(*rings_view);
    }

    auto cube = make_shared<PocketCube>();
    auto redraw_targets = make_shared<vector<Gtk::Widget*>>();

    auto describe_path = [](const vector<Move>& history) {
        if (history.empty()) {
            return string("路径：（尚未转动，仍是复原状态）");
        }
        string text = "路径：";
        for (size_t i = 0; i < history.size(); ++i) {
            if (i != 0) {
                text += ' ';
            }
            text += move_label(history[i]);
        }
        return text;
    };
    auto describe_solved = [](bool solved) {
        return string(solved ? "当前已复原" : "当前尚未复原");
    };

    Gtk::Label* path_label = nullptr;
    Gtk::Label* solved_label = nullptr;
    Gtk::Widget* current_view_3d = nullptr;
    auto current_view_animation = make_shared<optional<TurnAnimation>>();
    if (current_host) {
        // 尺寸比"操作视角"三个小面板（140px）明显大一圈——这里
        // 是唯一展示"现在真实是什么状态"的地方，不该比旁边的小面板更小。
        auto* view_3d = make_cube_3d_view(
            [cube] { return cube->state(); },
            320,
            [current_view_animation] { return *current_view_animation; });
        auto* view_net = make_cube_net_view(
            [cube] { return cube->state(); }, 320, 240);
        current_host->append(*view_3d);
        current_host->append(*view_net);
        redraw_targets->push_back(view_3d);
        redraw_targets->push_back(view_net);
        current_view_3d = view_3d;

        auto summary = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 8);
        summary->set_valign(Gtk::Align::CENTER);
        summary->set_size_request(220, -1);

        auto space_label = Gtk::make_managed<Gtk::Label>(
            "状态空间数量："
            + format_thousands(kCubeStateSpaceSizeIgnoringOrientation)
            + " 种\n（不计整体朝向）");
        space_label->set_halign(Gtk::Align::START);
        space_label->set_wrap(true);
        space_label->set_xalign(0);
        space_label->add_css_class("dim-label");
        summary->append(*space_label);

        path_label =
            Gtk::make_managed<Gtk::Label>(describe_path(cube->move_history()));
        path_label->set_halign(Gtk::Align::START);
        path_label->set_xalign(0);
        path_label->set_wrap(true);
        summary->append(*path_label);

        solved_label =
            Gtk::make_managed<Gtk::Label>(describe_solved(is_solved(cube->state())));
        solved_label->set_halign(Gtk::Align::START);
        solved_label->set_xalign(0);
        summary->append(*solved_label);
        current_host->append(*summary);
    }

    // 操作视角：U/R/F 三个面各自的 2x2 小面板，只读展示"这个操作面现在
    // 是什么颜色"，不是预测转完之后的样子——之前这里是九宫格预测九种
    // 转法的结果，反馈是这个九宫格容易干扰，换成只看当前状态。
    if (next_grid_host) {
        auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 10);
        row->set_hexpand(true);
        row->set_vexpand(true);
        const array<pair<Face, string>, 3> panels = {{
            {Face::U, "上 U"},
            {Face::R, "右 R"},
            {Face::F, "前 F"},
        }};
        for (const auto& [face, caption] : panels) {
            auto* panel = make_operation_face_panel(
                [cube] { return cube->state(); }, face, caption, *redraw_targets);
            row->append(*panel);
        }
        next_grid_host->append(*row);
    }

    // 操作区：九个转法按钮，跟“操作视角”三个面板共用同一份
    // next_move_set()，不是另外维护一份转法列表；按钮标签用
    // move_label()（Singmaster 记号，如 "U'"），tooltip 用
    // move_description()（记号+中文注解），跟九宫格每格的标注同一套
    // 文案来源。
    vector<Gtk::Button*> operation_buttons;
    if (operations_host) {
        auto grid = Gtk::make_managed<Gtk::Grid>();
        grid->set_row_spacing(10);
        grid->set_column_spacing(10);
        grid->set_row_homogeneous(true);
        grid->set_column_homogeneous(true);
        grid->set_hexpand(true);
        grid->set_vexpand(true);

        const array<Move, 9> moves = next_move_set();
        for (size_t i = 0; i < moves.size(); ++i) {
            const Move move = moves[i];
            auto* button = Gtk::make_managed<Gtk::Button>(move_label(move));
            button->add_css_class("btn-outline-secondary");
            button->set_tooltip_text(move_description(move));
            // 按钮跟着格子一起撑满，不是缩在格子中间一小块——“操作区”
            // 这块地方本来就是让九个按钮占满的，不是给别的内容留白。
            button->set_hexpand(true);
            button->set_vexpand(true);
            operation_buttons.push_back(button);
            grid->attach(*button, static_cast<int>(i % 3), static_cast<int>(i / 3));
        }
        operations_host->append(*grid);
    }

    const auto refresh_cube_display =
        [cube,
         redraw_targets,
         path_label,
         solved_label,
         describe_path,
         describe_solved]() {
            for (auto* widget : *redraw_targets) {
                widget->queue_draw();
            }
            if (path_label) {
                path_label->set_text(describe_path(cube->move_history()));
            }
            if (solved_label) {
                solved_label->set_text(
                    describe_solved(is_solved(cube->state())));
            }
        };

    // 九个按钮共享同一个 current_view_3d/current_view_animation，同一时刻
    // 只能播一个转动动画，点下去先把全部九个按钮禁用，动画播完（真正
    // apply_turn() 改了状态之后）再一起解禁——避免动画播到一半又点了
    // 另一个按钮，两次转动的动画状态互相打架。
    const auto set_operation_buttons_sensitive = [operation_buttons](bool sensitive) {
        for (auto* button : operation_buttons) {
            button->set_sensitive(sensitive);
        }
    };

    for (size_t i = 0; i < operation_buttons.size(); ++i) {
        const Move move = next_move_set()[i];
        operation_buttons[i]->signal_clicked().connect(
            [cube,
             move,
             refresh_cube_display,
             current_view_3d,
             current_view_animation,
             rings_view,
             rings_animation,
             set_operation_buttons_sensitive]() {
                const auto finish_turn = [cube, move, refresh_cube_display,
                                           set_operation_buttons_sensitive]() {
                    cube->apply_turn(move);
                    refresh_cube_display();
                    set_operation_buttons_sensitive(true);
                };

                if (current_view_3d) {
                    set_operation_buttons_sensitive(false);
                    play_turn_animation(
                        current_view_3d, current_view_animation, move, false,
                        finish_turn, rings_view, rings_animation);
                } else {
                    finish_turn();
                }
            });
    }

    if (reset_button) {
        reset_button->signal_clicked().connect(
            [cube, refresh_cube_display]() {
                cube->reset();
                refresh_cube_display();
            });
    }
}

} // namespace

int main(int argc, char* argv[]) {
    auto app = Gtk::Application::create("cn.athena.practice.pocketcube");
    app->signal_activate().connect([app] {
        auto builder = Gtk::Builder::create_from_resource("/app/window.ui");
        auto* window = builder->get_widget<Gtk::ApplicationWindow>("window");
        if (window == nullptr) {
            return;
        }
        wire_window(builder);
        app->add_window(*window);
        window->present();
    });
    return app->run(argc, argv);
}
