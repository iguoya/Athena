#include "chapter_nav_strip.h"

#include "ui/icon_utils.h"

#include <utility>
#include <vector>

using namespace std;

ChapterNavStrip::ChapterNavStrip(Gtk::FlowBox& tab_box, Gtk::Stack& stack)
    : m_tab_box(tab_box), m_stack(stack) {}

void ChapterNavStrip::reset() {
    for (auto* button : m_tabs) {
        m_tab_box.remove(*button);
    }
    m_tabs.clear();
    m_button_by_key.clear();

    vector<string> transient;
    for (const auto& key : m_page_keys) {
        if (m_persistent_keys.count(key) == 0) {
            transient.push_back(key);
        }
    }
    for (const auto& key : transient) {
        if (auto* child = m_stack.get_child_by_name(key)) {
            m_stack.remove(*child);
        }
        m_page_keys.erase(key);
    }
    m_current_key.clear();
}

void ChapterNavStrip::add_tab(
    const TabSpec& spec,
    function<void()> on_activate) {
    auto* button = Gtk::make_managed<Gtk::ToggleButton>();
    button->add_css_class("pill");
    button->add_css_class("chapter-tab");
    button->set_tooltip_text(spec.tooltip);

    auto* content = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, 6);
    content->append(*make_icon_image(spec.icon, 16));
    content->append(*Gtk::make_managed<Gtk::Label>(spec.label));
    button->set_child(*content);

    if (!m_tabs.empty()) {
        button->set_group(*m_tabs.front());
    }
    button->signal_toggled().connect(
        [this, button, callback = std::move(on_activate)]() {
            if (button->get_active() && !m_suppress_activate) {
                callback();
            }
        });

    m_tab_box.append(*button);
    m_tabs.push_back(button);
    if (!spec.key.empty()) {
        m_button_by_key[spec.key] = button;
    }
}

void ChapterNavStrip::set_page(
    const string& key,
    Gtk::Widget& widget,
    const string& title,
    Persistence persistence) {
    if (auto* existing = m_stack.get_child_by_name(key)) {
        m_stack.remove(*existing);
    }
    m_stack.add(widget, key, title);
    m_page_keys.insert(key);
    if (persistence == Persistence::Persistent) {
        m_persistent_keys.insert(key);
    }
}

void ChapterNavStrip::set_placeholder(const string& key, const string& title) {
    if (m_stack.get_child_by_name(key)) {
        return;
    }
    m_stack.add(*Gtk::make_managed<Gtk::Box>(), key, title);
    m_page_keys.insert(key);
}

bool ChapterNavStrip::has_page(const string& key) const {
    return m_page_keys.count(key) > 0;
}

void ChapterNavStrip::show(const string& key) {
    const auto button = m_button_by_key.find(key);
    if (button != m_button_by_key.end() && !button->second->get_active()) {
        m_suppress_activate = true;
        button->second->set_active(true);
        m_suppress_activate = false;
    }
    reveal(key);
}

void ChapterNavStrip::reveal(const string& key) {
    if (m_stack.get_child_by_name(key)) {
        m_stack.set_visible_child(key);
        m_current_key = key;
    }
}

void ChapterNavStrip::activate_first() {
    if (!m_tabs.empty()) {
        m_tabs.front()->set_active(true);
    }
}
