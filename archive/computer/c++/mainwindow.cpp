#include "mainwindow.h"

MainWindow* MainWindow::window;
MainWindow::MainWindow(GtkApplicationWindow *cobject,
                       const Glib::RefPtr<Gtk::Builder> &refBuilder)
    : Gtk::ApplicationWindow(cobject), builder(refBuilder) {
    set_default_size(1600, 1200);

    builder->get_widget("treeview_menu", menu);
    menu->set_model(menuModel.model);
    menu->expand_all();
    menu->get_selection()->signal_changed().connect(
                sigc::mem_fun(*this, &MainWindow::on_selected));


    builder->get_widget("textview", textView);
    textBuffer = Glib::RefPtr<Gtk::TextBuffer>::cast_dynamic(
                builder->get_object("textbuffer"));
    //    textBuffer = Gtk::TextBuffer::create();
    textView->set_buffer(textBuffer);

    SModelColumns model(10);
    builder->get_widget("listview", listView);
    for(size_t i = 0; i < model.columns.size(); ++i) {
        listView->append_column(to_string(i), model.columns[i]);
        listView->get_column(i)->set_expand(true);
    }

    //    auto m = listView->get_column(1);
    //    m->set_title("KKKK");

    //    for(auto m : listView->get_columns()) {
    //        m->set_title("AAAA");
    //        cout<<"sssss"<<endl;
    //    }

    listStore = Gtk::ListStore::create(model);
    listView->set_model(listStore);

    builder->get_widget("treeview", treeView);
    //    show_all_children();
    //        auto styleProvider = Gtk::CssProvider::create();
    //        styleProvider->load_from_resource("/style.css");

    //        auto screen = Gdk::Display::get_default();
    //        auto context = window->get_style_context();

    //  context->add_provider_for_display(screen, styleProvider, 800);
}

MainWindow* MainWindow::create()
{
//    auto builder = Gtk::Builder::create_from_resource("/window.glade");
    auto builder = Gtk::Builder::create_from_file("window.glade");

    builder->get_widget_derived("window", window);
    return window;
}

void MainWindow::on_selected() {
    auto iter = menu->get_selection()->get_selected();
    if (iter) // If anything is selected
    {
        auto row = *iter;
//        cout << row[column.name] << "-----"
//             << row[column.description] << "-----" << std::endl;
        //        auto product = Factory::create(row.get_value(column.identifier));
        auto product = (Product*)Factory::GetInstance()->CreateObject(row.get_value(column.identifier));
        if(product != nullptr) {
            product->display.connect(sigc::mem_fun(*this,
                                                   &MainWindow::display));
            product->displays.connect(sigc::mem_fun(*this,
                                                    &MainWindow::displays));

            product->displayTable.connect(sigc::mem_fun(*this,
                                                        &MainWindow::displayTable));

            product->run();
        }
    }
}

void MainWindow::display(string msg)
{
    textBuffer->insert_at_cursor(msg+"\n");
}

void MainWindow::displays(vector<string> msgs)
{
    for(auto msg : msgs) {
        textBuffer->insert_at_cursor(msg+"\n");
    }
}

void MainWindow::displayTable(vector<string> columns, vector<vector<string> > result)
{

    size_t i = 0;
    for(auto column : listView->get_columns()) {
        if(i >= columns.size()) {
            column->set_title("");
        } else {
            column->set_title(columns[i]);
//            column->set_expand(true);
        }
        ++i;
    }

//    listStore->clear();

    for(auto record : result) {
        auto row = *(listStore->append());
        for(size_t i = 0; i < record.size(); ++i) {
            row.set_value<ustring>(static_cast<int>(i), record[i]);
        }
    }
}

MainWindow::SModelColumns::SModelColumns(size_t n)
{
    columns.resize(n);
    for(size_t i = 0; i < n; ++i) {
        add(columns[i]);
    }
}
