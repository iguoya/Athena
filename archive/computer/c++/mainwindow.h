#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <gtkmm.h>
#include <giomm.h>
#include "assert.h"
#include "menumodel.h"
#include <iostream>
#include "factory.h"
#include "product.h"
using namespace std;
using namespace Glib;

class MainWindow : public Gtk::ApplicationWindow
{
public:
    MainWindow(GtkApplicationWindow* cobject, const Glib::RefPtr<Gtk::Builder>& refBuilder);
    static MainWindow* create();
protected:
    void on_selected();
    void display(string msg);
    void displays(vector<string> msgs);
    void displayTable(vector<string> columns,
                      vector<vector<string>> result);
private:
    RefPtr<Gtk::Builder> builder;
    static MainWindow* window;

    Gtk::TreeView* menu;
    MenuModel menuModel;
    ModelColumns column;

    Gtk::TreeView* listView;
    RefPtr<Gtk::ListStore> listStore;
    Gtk::TreeView* treeView;
    RefPtr<Gtk::TreeStore> treeStore;

    Gtk::TextView* textView;
    Glib::RefPtr<Gtk::TextBuffer> textBuffer;
    RefPtr<Gtk::TextBuffer::Mark> m_endMark;

    class SModelColumns : public Gtk::TreeModel::ColumnRecord
    {
    public:
        SModelColumns(size_t n);
        vector<Gtk::TreeModelColumn<Glib::ustring>> columns;
    };
};


#endif // MAINWINDOW_H
