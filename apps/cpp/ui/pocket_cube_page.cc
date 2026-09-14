#include "pocket_cube_page.h"

#include "practice/pocket_cube/pocket_cube.hpp"
#include "practice/pocket_cube/view.h"
#include "ui/icon_utils.h"
#include "ui/source_view.h"

#include <algorithm>
#include <chrono>
#include <functional>
#include <memory>
#include <optional>
#include <sstream>
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

void play_turn_animation(
    Gtk::Widget* view_3d,
    shared_ptr<optional<TurnAnimation>> animation_state,
    Move move,
    bool reverse,
    function<void()> on_complete) {
    const FaceLayout layout = face_layout(move.face);
    const double target_degrees = turn_angle_degrees(move);
    const double start_degrees = reverse ? target_degrees : 0.0;
    const double end_degrees = reverse ? 0.0 : target_degrees;

    *animation_state =
        TurnAnimation{layout.normal_axis, layout.normal_sign, start_degrees};
    view_3d->queue_draw();

    const auto started = chrono::steady_clock::now();
    Glib::signal_timeout().connect(
        [animation_state, view_3d, started, start_degrees, end_degrees,
         on_complete]() -> bool {
            const double elapsed_ms = chrono::duration<double, milli>(
                                          chrono::steady_clock::now() - started)
                                          .count();
            const double progress = min(1.0, elapsed_ms / kTurnAnimationMs);
            if (*animation_state) {
                (*animation_state)->current_degrees =
                    start_degrees + (end_degrees - start_degrees) * progress;
            }
            view_3d->queue_draw();
            if (progress >= 1.0) {
                *animation_state = nullopt;
                on_complete();
                return false;
            }
            return true;
        },
        kTurnAnimationFrameMs);
}

Gtk::Widget* make_cube_state_block(
    function<CubeState()> next_state_provider,
    int view_3d_size,
    int net_width,
    int net_height,
    const string& caption,
    vector<Gtk::Widget*>& redraw_targets,
    vector<Gtk::ToggleButton*>& restore_buttons,
    function<CubeState()> current_state_provider,
    Move move) {
    auto show_current = make_shared<bool>(false);
    function<CubeState()> effective_provider =
        [next_state_provider, current_state_provider, show_current]() {
            return *show_current ? current_state_provider() : next_state_provider();
        };

    auto box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 4);
    box->set_hexpand(true);
    box->set_vexpand(true);
    box->set_halign(Gtk::Align::FILL);
    box->set_valign(Gtk::Align::FILL);
    box->set_margin(6);

    auto views_row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    views_row->set_hexpand(true);
    views_row->set_vexpand(true);

    auto cell_animation = make_shared<optional<TurnAnimation>>();
    auto* view_3d = make_cube_3d_view(
        effective_provider, view_3d_size,
        [cell_animation] { return *cell_animation; });
    auto* view_net = make_cube_net_view(
        effective_provider, net_width, net_height);
    view_3d->set_hexpand(true);
    view_3d->set_vexpand(true);
    view_net->set_hexpand(true);
    view_net->set_vexpand(true);
    views_row->append(*view_3d);
    views_row->append(*view_net);
    box->append(*views_row);
    redraw_targets.push_back(view_3d);
    redraw_targets.push_back(view_net);

    if (!caption.empty()) {
        auto label = Gtk::make_managed<Gtk::Label>(caption);
        label->add_css_class("caption");
        label->add_css_class("dim-label");
        label->set_halign(Gtk::Align::CENTER);
        label->set_wrap(true);
        label->set_justify(Gtk::Justification::CENTER);
        box->append(*label);
    }

    auto restore_button = Gtk::make_managed<Gtk::ToggleButton>();
    restore_button->set_icon_name("view-refresh-symbolic");
    restore_button->add_css_class("flat");
    restore_button->set_halign(Gtk::Align::END);
    restore_button->set_valign(Gtk::Align::END);
    restore_button->set_margin(4);
    restore_button->set_tooltip_text(
        "按下：改看当前实际状态；再按一次：切回这一步转完的样子");
    restore_buttons.push_back(restore_button);
    restore_button->signal_toggled().connect(
        [show_current, restore_button, view_3d, view_net, cell_animation, move]() {
            const bool next_show_current = restore_button->get_active();
            restore_button->set_sensitive(false);
            play_turn_animation(
                view_3d,
                cell_animation,
                move,
                next_show_current,
                [show_current, next_show_current, view_net, restore_button]() {
                    *show_current = next_show_current;
                    view_net->queue_draw();
                    restore_button->set_sensitive(true);
                });
        });

    auto overlay = Gtk::make_managed<Gtk::Overlay>();
    overlay->set_child(*box);
    overlay->add_overlay(*restore_button);

    auto frame = Gtk::make_managed<Gtk::Frame>();
    frame->set_hexpand(true);
    frame->set_vexpand(true);
    frame->add_css_class("panel-frame");
    frame->set_child(*overlay);
    return frame;
}

} // namespace

PocketCubePage::PocketCubePage(
    const ChapterMeta& chapter,
    const Glib::RefPtr<Gtk::Builder>& builder,
    const ContentLoader& content_loader,
    function<void()> on_overview_requested) {
    auto title_label = builder->get_widget<Gtk::Label>("chapter_title_label");
    auto description_label =
        builder->get_widget<Gtk::Label>("chapter_description_label");
    auto chapter_icon = builder->get_widget<Gtk::Image>("chapter_icon");
    auto chapter_overview_button =
        builder->get_widget<Gtk::Button>("chapter_overview_button");
    auto source_view = GTK_SOURCE_VIEW(
        gtk_builder_get_object(builder->gobj(), "practice_source_view"));
    auto run_button = builder->get_widget<Gtk::Button>("practice_run_button");
    auto reset_button = builder->get_widget<Gtk::Button>("practice_reset_button");
    auto result_view =
        builder->get_widget<Gtk::TextView>("practice_result_view");
    auto current_host =
        builder->get_widget<Gtk::Box>("practice_cube_current_host");
    auto next_grid_host =
        builder->get_widget<Gtk::Box>("practice_cube_next_grid_host");

    if (title_label) {
        title_label->set_text(chapter.title);
    }
    if (description_label) {
        description_label->set_text(chapter.description);
    }
    if (chapter_icon) {
        configure_icon_image(*chapter_icon, chapter.icon, 36);
    }
    if (result_view) {
        result_view->get_buffer()->set_text("点击“运行”查看结果。");
    }
    if (!chapter.subchapters.empty()) {
        display_project_source(
            source_view,
            content_loader,
            chapter.source,
            chapter.subchapters.front().name);
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
        auto* view_3d = make_cube_3d_view(
            [cube] { return cube->state(); },
            200,
            [current_view_animation] { return *current_view_animation; });
        auto* view_net = make_cube_net_view(
            [cube] { return cube->state(); }, 220, 165);
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

    vector<Gtk::ToggleButton*> restore_buttons;
    if (next_grid_host) {
        auto grid = Gtk::make_managed<Gtk::Grid>();
        grid->set_row_spacing(10);
        grid->set_column_spacing(10);
        grid->set_row_homogeneous(true);
        grid->set_column_homogeneous(true);
        grid->set_hexpand(true);
        grid->set_vexpand(true);

        const auto initial_next_states = cube->next_states();
        for (size_t i = 0; i < initial_next_states.size(); ++i) {
            const Move move = initial_next_states[i].first;
            auto* cell = make_cube_state_block(
                [cube, i] { return cube->next_states()[i].second; },
                90,
                96,
                72,
                move_description(move),
                *redraw_targets,
                restore_buttons,
                [cube] { return cube->state(); },
                move);
            cell->set_tooltip_text(move_description(move));
            grid->attach(
                *cell, static_cast<int>(i % 3), static_cast<int>(i / 3));
        }
        next_grid_host->append(*grid);
    }

    if (chapter_overview_button) {
        chapter_overview_button->signal_clicked().connect(
            std::move(on_overview_requested));
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

    if (run_button && result_view) {
        run_button->signal_clicked().connect(
            [cube,
             result_view,
             refresh_cube_display,
             current_view_3d,
             current_view_animation,
             run_button]() {
                const auto finish_run =
                    [cube, result_view, refresh_cube_display, run_button]() {
                        ostringstream output;
                        cube->run(output);
                        result_view->get_buffer()->set_text(output.str());
                        refresh_cube_display();
                        run_button->set_sensitive(true);
                    };

                if (current_view_3d) {
                    run_button->set_sensitive(false);
                    play_turn_animation(
                        current_view_3d,
                        current_view_animation,
                        cube->next_turn_move(),
                        false,
                        finish_run);
                } else {
                    finish_run();
                }
            });
    }

    if (reset_button && result_view) {
        reset_button->signal_clicked().connect(
            [cube, result_view, refresh_cube_display, restore_buttons]() {
                cube->reset();
                result_view->get_buffer()->set_text(
                    "已重置为初始（已复原）状态。");
                refresh_cube_display();
                for (auto* button : restore_buttons) {
                    button->set_active(false);
                }
            });
    }
}
