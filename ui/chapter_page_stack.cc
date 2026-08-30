#include "chapter_page_stack.h"

#include <vector>

using namespace std;

ChapterPageStack::ChapterPageStack(Gtk::Stack& stack) : m_stack(stack) {}

void ChapterPageStack::reset() {
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

void ChapterPageStack::set_page(
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

void ChapterPageStack::set_placeholder(const string& key, const string& title) {
    if (m_stack.get_child_by_name(key)) {
        return;
    }
    m_stack.add(*Gtk::make_managed<Gtk::Box>(), key, title);
    m_page_keys.insert(key);
}

bool ChapterPageStack::has_page(const string& key) const {
    return m_page_keys.count(key) > 0;
}

void ChapterPageStack::show(const string& key) {
    if (m_stack.get_child_by_name(key)) {
        m_stack.set_visible_child(key);
        m_current_key = key;
    }
}
