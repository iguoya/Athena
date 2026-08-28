#include "about_dialog.h"

#include "ui/dialog_helpers.h"

#include <string>

using namespace std;

AboutDialog::AboutDialog(Gtk::Window& parent) : m_parent(parent) {}

void AboutDialog::present() {
    ensure_created();
    m_parent.set_sensitive(false);
    m_dialog->present();
}

void AboutDialog::ensure_created() {
    if (m_dialog) {
        return;
    }

    m_dialog = make_unique<Gtk::Dialog>();
    m_dialog->set_title("关于 Athena");
    m_dialog->set_default_size(440, 480);

    auto* content = m_dialog->get_content_area();
    auto page = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 14);
    page->set_margin_top(20);
    page->set_margin_bottom(20);
    page->set_margin_start(24);
    page->set_margin_end(24);
    content->append(*page);

    auto header = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 14);
    auto icon = Gtk::make_managed<Gtk::Image>();
    icon->set_from_icon_name("cn.athena.icon");
    icon->set_pixel_size(48);
    header->append(*icon);

    auto title_box = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::VERTICAL, 3);
    title_box->set_valign(Gtk::Align::CENTER);
    auto name_label = Gtk::make_managed<Gtk::Label>("Athena");
    name_label->add_css_class("title-2");
    name_label->set_halign(Gtk::Align::START);
    title_box->append(*name_label);
    auto version_label =
        Gtk::make_managed<Gtk::Label>(string("版本 ") + ATHENA_VERSION);
    version_label->add_css_class("dim-label");
    version_label->set_halign(Gtk::Align::START);
    title_box->append(*version_label);
    header->append(*title_box);
    page->append(*header);

    auto comments = Gtk::make_managed<Gtk::Label>(
        "为快速渐进学习和掌握 C++ 而开发的自用软件平台，突出学练合一："
        "把零散的代码知识点学习整合到统一框架中，方便运行验证和自我修正。");
    comments->add_css_class("dim-label");
    comments->set_wrap(true);
    comments->set_halign(Gtk::Align::START);
    page->append(*comments);

    auto copyright_label =
        Gtk::make_managed<Gtk::Label>("Copyright (c) 2026 tiger");
    copyright_label->add_css_class("dim-label");
    copyright_label->set_halign(Gtk::Align::START);
    page->append(*copyright_label);

    auto license_frame = Gtk::make_managed<Gtk::Frame>();
    license_frame->add_css_class("panel-frame");
    license_frame->set_vexpand(true);
    auto license_scroll = Gtk::make_managed<Gtk::ScrolledWindow>();
    license_scroll->set_policy(
        Gtk::PolicyType::NEVER, Gtk::PolicyType::AUTOMATIC);
    auto license_label = Gtk::make_managed<Gtk::Label>(
        "Athena is licensed under Mulan PSL v2.\n"
        "You can use this software according to the terms and "
        "conditions of the Mulan PSL v2.\n"
        "You may obtain a copy of Mulan PSL v2 at:\n"
        "    http://license.coscl.org.cn/MulanPSL2\n\n"
        "THIS SOFTWARE IS PROVIDED ON AN \"AS IS\" BASIS, WITHOUT "
        "WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING "
        "BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT "
        "FOR A PARTICULAR PURPOSE.\n"
        "See the Mulan PSL v2 for more details.");
    license_label->add_css_class("dim-label");
    license_label->set_wrap(true);
    license_label->set_halign(Gtk::Align::START);
    license_label->set_margin(12);
    license_scroll->set_child(*license_label);
    license_frame->set_child(*license_scroll);
    page->append(*license_frame);

    auto close_button = Gtk::make_managed<Gtk::Button>("关闭");
    close_button->add_css_class("btn-primary");
    close_button->signal_clicked().connect(
        [dialog = m_dialog.get()]() { dialog->close(); });
    append_dialog_action_bar(content, {close_button});

    m_dialog->set_transient_for(m_parent);
    m_dialog->set_modal(true);
    m_dialog->set_hide_on_close(true);
    m_dialog->signal_hide().connect(
        [this]() { m_parent.set_sensitive(true); });
}
