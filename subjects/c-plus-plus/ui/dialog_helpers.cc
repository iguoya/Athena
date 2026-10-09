#include "ui/dialog_helpers.h"

void append_dialog_action_bar(
    Gtk::Box* content_box, const vector<Gtk::Button*>& extra_buttons) {
    if (extra_buttons.empty()) {
        return;
    }
    auto action_bar = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 8);
    action_bar->set_halign(Gtk::Align::CENTER);
    action_bar->add_css_class("dialog-action-bar");

    for (auto* button : extra_buttons) {
        action_bar->append(*button);
    }

    content_box->append(*action_bar);
}

void lock_for_modal_dialog(Gtk::Window& main_window, Gtk::Dialog& dialog) {
    dialog.set_transient_for(main_window);
    dialog.set_modal(true);
    dialog.set_hide_on_close(true);
    main_window.set_sensitive(false);
    dialog.signal_hide().connect([&main_window, &dialog]() {
        main_window.set_sensitive(true);
        Glib::signal_idle().connect_once([&dialog]() { delete &dialog; });
    });
    dialog.present();
}
