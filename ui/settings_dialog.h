#pragma once

#include "ui/api_key_store.h"

#include <gtkmm.h>

using namespace std;

// 设置面板：目前只有两个 AI 服务商 Key。独立成模块，只依赖父窗口和
// ApiKeyStore。
class SettingsDialog final {
public:
    SettingsDialog(Gtk::Window& parent, ApiKeyStore& api_keys);

    void show();

private:
    Gtk::Window& m_parent;
    ApiKeyStore& m_api_keys;
};
