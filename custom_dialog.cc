#include "custom_dialog.h"
#include <iostream>

CustomDialog::CustomDialog(AppWindow& parent)
    : Gtk::Window(),
      m_parent(parent) {
    
    auto builder = Gtk::Builder::create_from_file("ui/custom_dialog.ui");
    
    m_btn_ok = builder->get_widget<Gtk::Button>("btn_ok");
    m_btn_cancel = builder->get_widget<Gtk::Button>("btn_cancel");
    m_entry = builder->get_widget<Gtk::Entry>("entry");
    
    if (m_btn_ok) {
        m_btn_ok->signal_clicked().connect(
            sigc::mem_fun(*this, &CustomDialog::on_ok));
    }
    
    if (m_btn_cancel) {
        m_btn_cancel->signal_clicked().connect(
            sigc::mem_fun(*this, &CustomDialog::on_cancel));
    }
    
    auto main_widget = builder->get_widget<Gtk::Widget>("dialog_content");
    if (main_widget) {
        set_child(*main_widget);
    }
    
    set_title("Custom Dialog");
    set_transient_for(parent);
    set_modal(true);
    set_default_size(300, 200);
}

CustomDialog::~CustomDialog() {
    cout << "CustomDialog destroyed" << endl;
}

void CustomDialog::on_ok() {
    cout << "Dialog OK: " << (m_entry ? m_entry->get_text() : "") << endl;
    m_signal_response.emit(GTK_RESPONSE_OK);
    hide();
}

void CustomDialog::on_cancel() {
    cout << "Dialog Cancel" << endl;
    m_signal_response.emit(GTK_RESPONSE_CANCEL);
    hide();
}

CustomDialog::type_signal_response CustomDialog::signal_response() {
    return m_signal_response;
}