// 临时探针：水平 Box 三个按钮在不同 hexpand / halign / spacing 下的 get_width。
// 不进演示。跑完打印到 stdout 并退出。

#include <gtkmm.h>

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

struct Step {
    const char* name;
    bool a;
    bool b;
    bool c;
    Gtk::Align align;
    int spacing;
    int request;
};

const Step kSteps[] = {
    {"none-480", false, false, false, Gtk::Align::FILL, 0, 480},
    {"b-fill-480", false, true, false, Gtk::Align::FILL, 0, 480},
    {"ab-fill-480", true, true, false, Gtk::Align::FILL, 0, 480},
    {"abc-fill-480", true, true, true, Gtk::Align::FILL, 0, 480},
    {"a-fill-480", true, false, false, Gtk::Align::FILL, 0, 480},
    {"b-center-480", false, true, false, Gtk::Align::CENTER, 0, 480},
    {"b-center-720", false, true, false, Gtk::Align::CENTER, 0, 720},
    {"b-fill-720", false, true, false, Gtk::Align::FILL, 0, 720},
    {"b-fill-sp16", false, true, false, Gtk::Align::FILL, 16, 480},
    {"b-center-sp16", false, true, false, Gtk::Align::CENTER, 16, 480},
    {"none-sp16", false, false, false, Gtk::Align::FILL, 16, 480},
    {"ab-fill-sp16", true, true, false, Gtk::Align::FILL, 16, 480},
    {"b-start-480", false, true, false, Gtk::Align::START, 0, 480},
    {"b-center-noexp", false, false, false, Gtk::Align::CENTER, 0, 480},
};

class Probe : public Gtk::Window {
public:
    Probe(int width, bool nest) : width_(width) {
        set_title("probe");
        set_default_size(width, nest ? 280 : 160);
        a_.set_label("甲");
        b_.set_label("乙");
        c_.set_label("丙");
        row_.append(a_);
        row_.append(b_);
        row_.append(c_);
        if (nest) {
            // 与演示相同的嵌套：垂直盒有边距，行在其他部件中间。
            root_.set_margin(12);
            root_.set_spacing(10);
            row_.set_hexpand(true);
            root_.append(root_hint_);
            root_.append(row_);
            set_child(root_);
        } else {
            set_child(row_);
        }
        arm_tick();
    }

    void arm_tick() {
        signal_realize().connect([this] {
            add_tick_callback([this](const Glib::RefPtr<Gdk::FrameClock>&) {
                on_tick();
                return keep_;
            });
        });
    }

private:
    void apply(const Step& step) {
        a_.set_hexpand(step.a);
        b_.set_hexpand(step.b);
        c_.set_hexpand(step.c);
        a_.set_halign(Gtk::Align::FILL);
        b_.set_halign(step.align);
        c_.set_halign(Gtk::Align::FILL);
        row_.set_spacing(step.spacing);
    }

    static int natural_of(Gtk::Widget& widget) {
        int min = 0, nat = 0, min_b = 0, nat_b = 0;
        widget.measure(Gtk::Orientation::HORIZONTAL, -1, min, nat, min_b, nat_b);
        return nat;
    }

    void on_tick() {
        if (index_ >= static_cast<int>(std::size(kSteps))) {
            keep_ = false;
            close();
            return;
        }
        const Step& step = kSteps[index_];
        if (!applied_) {
            apply(step);
            applied_ = true;
            stable_ = 0;
            seen_ = "";
            return;
        }
        const int aw = a_.get_width();
        const int bw = b_.get_width();
        const int cw = c_.get_width();
        const int rw = row_.get_width();
        if (aw <= 0 || rw <= 0) return;
        const std::string now = std::to_string(aw) + "," + std::to_string(bw) + "," +
                                std::to_string(cw) + "," + std::to_string(rw);
        if (now != seen_) {
            seen_ = now;
            stable_ = 1;
            return;
        }
        if (++stable_ < 3) return;

        auto bounds = [](Gtk::Widget& widget, Gtk::Widget& target) {
            const auto rect = widget.compute_bounds(target);
            if (!rect) return std::string("none");
            return std::to_string(rect->get_x()) + "+" + std::to_string(rect->get_width());
        };
        int amin = 0, anat = 0, ab0 = 0, ab1 = 0;
        a_.measure(Gtk::Orientation::HORIZONTAL, -1, amin, anat, ab0, ab1);
        std::cout << "W" << width_ << " " << step.name << " row=" << rw << " get=" << aw << "," << bw
                  << "," << cw << " min=" << amin << " nat=" << natural_of(a_) << ","
                  << natural_of(b_) << "," << natural_of(c_)
                  << " bounds=" << bounds(a_, row_) << "|" << bounds(b_, row_) << "|"
                  << bounds(c_, row_) << "\n";
        std::cout.flush();
        ++index_;
        applied_ = false;
    }

    int width_;
    Gtk::Box root_{Gtk::Orientation::VERTICAL};
    Gtk::Label root_hint_;
    Gtk::Box row_{Gtk::Orientation::HORIZONTAL};
    Gtk::Button a_, b_, c_;
    int index_ = 0;
    bool applied_ = false;
    bool keep_ = true;
    int stable_ = 0;
    std::string seen_;
};

}  // namespace

int main(int argc, char* argv[]) {
    const bool nest = argc > 1 && std::string(argv[1]) == "nest";
    const int width = nest ? 560 : (argc > 1 ? std::atoi(argv[1]) : 800);
    auto app = Gtk::Application::create("cn.athena.gtkmm.probe.box");
    auto window = std::make_shared<Probe>(width, nest);
    app->signal_activate().connect([&app, window] {
        window->set_application(app);
        window->signal_close_request().connect(
            [&app] {
                app->quit();
                return false;
            },
            false);
        window->show();
    });
    return app->run(0, nullptr);
}
