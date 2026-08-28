#include "learning_dialogs.h"

#include <utility>

using namespace std;

LearningDialogs::LearningDialogs(
    Gtk::Window& parent,
    const ContentLoader& content_loader,
    LearningStore* learning_store,
    shared_ptr<atomic_bool> ui_alive)
    : m_api_keys(learning_store),
      m_ai_markdown(parent, content_loader, ui_alive),
      m_settings(parent, m_api_keys),
      m_history(parent, content_loader, learning_store, m_api_keys, m_ai_markdown),
      m_quiz(parent, content_loader, m_api_keys, std::move(ui_alive)),
      m_insight(
          parent, content_loader, learning_store, m_api_keys, m_ai_markdown) {}
